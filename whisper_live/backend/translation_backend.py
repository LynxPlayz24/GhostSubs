import os
import json
import logging
import threading
import time
import queue
from typing import Dict, Any, Optional
import torch
from transformers import MarianMTModel, MarianTokenizer

from whisper_live.backend.base import ServeClientBase


class ServeClientTranslation(ServeClientBase):
    """
    Handles translation of completed transcription segments in a separate thread.
    Uses Helsinki-NLP OPUS-MT models (~74M params) for fast JA->EN translation.
    Reads from a queue populated by the transcription backend and sends translated
    segments back to the client via WebSocket.
    """
    
    # Class-level model cache to avoid loading multiple copies
    _model_lock = threading.Lock()
    _shared_model = None
    _shared_tokenizer = None
    
    def __init__(
        self,
        client_uid,
        websocket,
        translation_queue,
        target_language="en", 
        send_last_n_segments=10,
        model_name="Helsinki-NLP/opus-mt-ja-en",
    ):
        """
        Initialize the translation client.
        
        Args:
            client_uid (str): Unique identifier for the client
            websocket: WebSocket connection to the client
            translation_queue (queue.Queue): Queue containing completed segments to translate
            target_language (str): Target language code (default: "en" for English)
            send_last_n_segments (int): Number of recent translated segments to send
            model_name (str): OPUS-MT model from HuggingFace (default: ja->en)
        """
        super().__init__(client_uid, websocket, send_last_n_segments)
        self.translation_queue = translation_queue
        self.target_language = target_language
        self.model_name = model_name
        self.translated_segments = []
        self.translation_model = None
        self.tokenizer = None
        self.model_loaded = False
        self.load_translation_model()
        
    def load_translation_model(self):
        """Load the OPUS-MT translation model (~74M params, fast on CPU)."""
        try:
            with ServeClientTranslation._model_lock:
                # Reuse shared model if already loaded by another client
                if ServeClientTranslation._shared_model is not None:
                    self.translation_model = ServeClientTranslation._shared_model
                    self.tokenizer = ServeClientTranslation._shared_tokenizer
                    self.model_loaded = True
                    logging.info("Reusing shared OPUS-MT translation model")
                    return
                
                logging.info(f"Loading OPUS-MT translation model: {self.model_name}")
                
                # Load tokenizer and model
                self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
                self.translation_model = MarianMTModel.from_pretrained(self.model_name)
                self.translation_model.eval()  # Set to inference mode
                
                # Cache for reuse across clients
                ServeClientTranslation._shared_model = self.translation_model
                ServeClientTranslation._shared_tokenizer = self.tokenizer
                
                param_count = sum(p.numel() for p in self.translation_model.parameters()) / 1e6
                logging.info(f"OPUS-MT model loaded ({param_count:.0f}M params, CPU inference)")
                self.model_loaded = True
                
        except Exception as e:
            logging.error(f"Failed to load translation model: {e}")
            import traceback
            traceback.print_exc()
            self.translation_model = None
            self.tokenizer = None
            self.model_loaded = False
    
    def translate_text(self, text: str) -> str:
        """
        Translate a single text segment using OPUS-MT.
        
        Args:
            text (str): Text to translate (Japanese)
            
        Returns:
            str: Translated text (English) or original text if translation fails
        """
        if not self.model_loaded or not text.strip():
            return text
            
        try:
            # Tokenize and translate
            encoded = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.translation_model.generate(
                    **encoded, 
                    max_new_tokens=256, 
                    num_beams=2,
                )
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
        except Exception as e:
            logging.error(f"Translation failed for text '{text[:50]}...': {e}")
            return text
    
    def process_translation_queue(self):
        """
        Process segments from the translation queue.
        Continuously reads from the queue until None is received (exit signal).
        """
        logging.info(f"Starting translation processing for client {self.client_uid}")
        
        while not self.exit:
            try:
                # Get segment from queue with timeout
                segment = self.translation_queue.get(timeout=1.0)
                
                # Check for exit signal
                if segment is None:
                    logging.info(f"Received exit signal for translation client {self.client_uid}")
                    break
                    
                # Only translate completed segments
                if not segment.get("completed", False):
                    self.translation_queue.task_done()
                    continue
                    
                # Translate the segment
                original_text = segment.get("text", "")
                translated_text = self.translate_text(original_text)
                
                # Create translated segment
                translated_segment = {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": translated_text,
                    "completed": segment.get("completed", False),
                    "target_language": self.target_language
                }
                
                self.translated_segments.append(translated_segment)
                segments_to_send = self.prepare_translated_segments()
                self.send_translation_to_client(segments_to_send)
                
                self.translation_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error processing translation queue: {e}")
                continue
        
        logging.info(f"Translation processing ended for client {self.client_uid}")
    
    def prepare_translated_segments(self):
        """
        Prepare the last n translated segments to send to client.
        
        Returns:
            list: List of recent translated segments
        """
        if len(self.translated_segments) >= self.send_last_n_segments:
            return self.translated_segments[-self.send_last_n_segments:]
        return self.translated_segments[:]
    
    def send_translation_to_client(self, translated_segments):
        """
        Send translated segments to the client via WebSocket.
        
        Args:
            translated_segments (list): List of translated segments to send
        """
        try:
            self.websocket.send(
                json.dumps({
                    "uid": self.client_uid,
                    "translated_segments": translated_segments,
                })
            )
        except Exception as e:
            logging.error(f"[ERROR]: Sending translation data to client: {e}")
    
    def speech_to_text(self):
        """
        Override parent method to handle translation processing.
        This method will be called when the translation thread starts.
        """
        self.process_translation_queue()
    
    def set_target_language(self, language: str):
        """
        Change the target language for translation.
        Note: OPUS-MT models are language-pair specific.
        
        Args:
            language (str): New target language code
        """
        self.target_language = language
        logging.info(f"Target language set to: {language}")
    
    def cleanup(self):
        """Clean up translation resources."""
        logging.info(f"Cleaning up translation resources for client {self.client_uid}")
        self.exit = True
        
        try:
            self.translation_queue.put(None, timeout=1.0)
        except:
            pass
        
        self.translated_segments.clear()
        # Note: shared model/tokenizer are kept alive for other clients
