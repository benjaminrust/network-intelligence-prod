import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self):
        self.cohere_url = os.getenv('COHERE_URL')
        self.cohere_api_key = os.getenv('COHERE_KEY')
        self.model_name = os.getenv("COHERE_MODEL_ID", "cohere-embed-multilingual")
        
        if not self.cohere_url or not self.cohere_api_key:
            logger.warning("Cohere credentials not found. Embedding generation will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Embedding manager initialized with Cohere")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for given text using Cohere"""
        if not self.enabled:
            logger.warning("Embedding generation disabled - no Cohere credentials")
            return None
        
        # Truncate text if it exceeds Cohere's 2048 character limit
        text = self._truncate_text_for_embedding(text)
        
        try:
            headers = {
                'Authorization': f'Bearer {self.cohere_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'input': [text],
                'model': self.model_name,
                'input_type': 'search_document'
            }
            
            response = requests.post(
                f"{self.cohere_url}/v1/embeddings",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Cohere API response: {result}")
                embeddings = result.get("data", [])
                if embeddings:
                    return embeddings[0].get("embedding", [])
                else:
                    logger.error("No embeddings returned from Cohere")
                    return None
            else:
                logger.error(f"Cohere API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def _truncate_text_for_embedding(self, text: str, max_length: int = 2000) -> str:
        """Truncate text to fit within Cohere's character limit"""
        if len(text) <= max_length:
            return text
        
        # Truncate and add indicator
        truncated = text[:max_length-20] + "... [truncated]"
        logger.warning(f"Text truncated from {len(text)} to {len(truncated)} characters for embedding")
        return truncated
    
    def generate_traffic_analysis_embedding(self, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate embedding for traffic analysis data"""
        # Create a comprehensive text description for the analysis
        text_description = self._create_analysis_description(analysis_data)
        
        # Generate embedding
        embedding = self.generate_embedding(text_description)
        
        if embedding:
            return {
                'analysis_type': analysis_data.get('analysis_type', 'traffic_analysis'),
                'source_data': analysis_data,
                'text_description': text_description,
                'embedding': embedding,
                'risk_score': analysis_data.get('risk_score', 0),
                'similarity_threshold': 0.8,
                'metadata': {
                    'model_used': self.model_name,
                    'embedding_dimensions': len(embedding),
                    'generated_at': analysis_data.get('timestamp')
                }
            }
        else:
            logger.error("Failed to generate embedding for traffic analysis")
            return None
    
    def generate_security_event_embedding(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate embedding for security event data"""
        # Create text description for the security event
        text_description = self._create_event_description(event_data)
        
        # Generate embedding
        embedding = self.generate_embedding(text_description)
        
        if embedding:
            return {
                'event_type': event_data.get('event_type'),
                'severity': event_data.get('severity'),
                'source_ip': event_data.get('source_ip'),
                'risk_score': event_data.get('risk_score', 0),
                'embedding': embedding,
                'text_description': text_description,
                'metadata': {
                    'model_used': self.model_name,
                    'embedding_dimensions': len(embedding)
                }
            }
        else:
            logger.error("Failed to generate embedding for security event")
            return None
    
    def generate_network_metric_embedding(self, metric_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate embedding for network metric data"""
        # Create text description for the network metric
        text_description = self._create_metric_description(metric_data)
        
        # Generate embedding
        embedding = self.generate_embedding(text_description)
        
        if embedding:
            return {
                'metric_name': metric_data.get('metric_name'),
                'metric_value': metric_data.get('metric_value'),
                'source': metric_data.get('source'),
                'embedding': embedding,
                'text_description': text_description,
                'metadata': {
                    'model_used': self.model_name,
                    'embedding_dimensions': len(embedding)
                }
            }
        else:
            logger.error("Failed to generate embedding for network metric")
            return None
    
    def _create_analysis_description(self, analysis_data: Dict[str, Any]) -> str:
        """Create a comprehensive text description for traffic analysis"""
        description_parts = []
        
        # Basic analysis info
        description_parts.append(f"Traffic analysis of type: {analysis_data.get('analysis_type', 'unknown')}")
        
        # Network statistics
        if 'network_stats' in analysis_data:
            stats = analysis_data['network_stats']
            description_parts.append(f"Network statistics: {stats.get('total_connections', 0)} total connections, "
                                   f"{stats.get('suspicious_connections', 0)} suspicious connections, "
                                   f"{stats.get('blocked_attempts', 0)} blocked attempts")
        
        # Risk assessment
        risk_score = analysis_data.get('risk_score', 0)
        description_parts.append(f"Risk assessment: {risk_score} risk score")
        
        # IP addresses involved
        if 'source_ip' in analysis_data:
            description_parts.append(f"Source IP: {analysis_data['source_ip']}")
        if 'destination_ip' in analysis_data:
            description_parts.append(f"Destination IP: {analysis_data['destination_ip']}")
        
        # Protocol and port information
        if 'protocol' in analysis_data:
            description_parts.append(f"Protocol: {analysis_data['protocol']}")
        if 'source_port' in analysis_data:
            description_parts.append(f"Source port: {analysis_data['source_port']}")
        if 'destination_port' in analysis_data:
            description_parts.append(f"Destination port: {analysis_data['destination_port']}")
        
        # Threat indicators
        if 'threat_indicators' in analysis_data:
            indicators = analysis_data['threat_indicators']
            if isinstance(indicators, list) and indicators:
                description_parts.append(f"Threat indicators detected: {', '.join(indicators)}")
        
        # Geographic information
        if 'country_code' in analysis_data:
            description_parts.append(f"Geographic origin: {analysis_data['country_code']}")
        if 'city' in analysis_data:
            description_parts.append(f"City: {analysis_data['city']}")
        
        # Timestamp
        if 'timestamp' in analysis_data:
            description_parts.append(f"Analysis timestamp: {analysis_data['timestamp']}")
        
        return ". ".join(description_parts)
    
    def _create_event_description(self, event_data: Dict[str, Any]) -> str:
        """Create a text description for security event"""
        description_parts = []
        
        # Event type and severity
        description_parts.append(f"Security event: {event_data.get('event_type', 'unknown')} with {event_data.get('severity', 'medium')} severity")
        
        # IP information
        if 'source_ip' in event_data:
            description_parts.append(f"Source IP: {event_data['source_ip']}")
        if 'destination_ip' in event_data:
            description_parts.append(f"Destination IP: {event_data['destination_ip']}")
        
        # Risk score
        risk_score = event_data.get('risk_score', 0)
        description_parts.append(f"Risk score: {risk_score}")
        
        # Protocol and ports
        if 'protocol' in event_data:
            description_parts.append(f"Protocol: {event_data['protocol']}")
        if 'source_port' in event_data:
            description_parts.append(f"Source port: {event_data['source_port']}")
        if 'destination_port' in event_data:
            description_parts.append(f"Destination port: {event_data['destination_port']}")
        
        # Geographic information
        if 'country_code' in event_data:
            description_parts.append(f"Country: {event_data['country_code']}")
        if 'city' in event_data:
            description_parts.append(f"City: {event_data['city']}")
        
        # User agent
        if 'user_agent' in event_data:
            description_parts.append(f"User agent: {event_data['user_agent']}")
        
        return ". ".join(description_parts)
    
    def _create_metric_description(self, metric_data: Dict[str, Any]) -> str:
        """Create a text description for network metric"""
        description_parts = []
        
        # Metric name and value
        metric_name = metric_data.get('metric_name', 'unknown')
        metric_value = metric_data.get('metric_value', 0)
        metric_unit = metric_data.get('metric_unit', '')
        
        description_parts.append(f"Network metric: {metric_name} = {metric_value} {metric_unit}")
        
        # Source and period
        if 'source' in metric_data:
            description_parts.append(f"Source: {metric_data['source']}")
        if 'period' in metric_data:
            description_parts.append(f"Period: {metric_data['period']}")
        
        # Tags
        if 'tags' in metric_data and metric_data['tags']:
            tags = metric_data['tags']
            if isinstance(tags, dict):
                tag_descriptions = [f"{k}: {v}" for k, v in tags.items()]
                description_parts.append(f"Tags: {', '.join(tag_descriptions)}")
        
        return ". ".join(description_parts)
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        if not self.enabled:
            logger.warning("Embedding generation disabled - no Cohere credentials")
            return [None] * len(texts)
        
        try:
            headers = {
                'Authorization': f'Bearer {self.cohere_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'input': texts,
                'model': self.model_name,
                'input_type': 'search_document'
            }
            
            response = requests.post(
                f"{self.cohere_url}/v1/embeddings",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = result.get("data", [])
                return [emb.get("embedding", []) for emb in embeddings]
            else:
                logger.error(f"Cohere API error: {response.status_code} - {response.text}")
                return [None] * len(texts)
                
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)
    
    def generate_guidance_embedding(self, guidance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate embedding for Claude guidance response"""
        # Create a comprehensive text description for the guidance
        text_description = self._create_guidance_description(guidance_data)
        
        # Generate embedding
        embedding = self.generate_embedding(text_description)
        
        if embedding:
            return {
                'request_id': guidance_data.get('request_id'),
                'source_ip': guidance_data.get('source_ip'),
                'risk_score': guidance_data.get('risk_score', 0),
                'threats_detected': guidance_data.get('threats_detected', []),
                'recommendations': guidance_data.get('recommendations', []),
                'claude_response': guidance_data.get('claude_response'),
                'embedding': embedding,
                'model_used': guidance_data.get('model_used', 'claude-3-5-sonnet-20241022'),
                'response_tokens': guidance_data.get('response_tokens'),
                'processing_time_ms': guidance_data.get('processing_time_ms'),
                'metadata': {
                    'model_used': self.model_name,
                    'embedding_dimensions': len(embedding),
                    'generated_at': guidance_data.get('timestamp'),
                    'text_description': text_description
                }
            }
        else:
            logger.error("Failed to generate embedding for guidance response")
            return None
    
    def _create_guidance_description(self, guidance_data: Dict[str, Any]) -> str:
        """Create a comprehensive text description for guidance data"""
        source_ip = guidance_data.get('source_ip', 'Unknown')
        risk_score = guidance_data.get('risk_score', 0)
        threats = guidance_data.get('threats_detected', [])
        recommendations = guidance_data.get('recommendations', [])
        claude_response = guidance_data.get('claude_response', '')
        
        # Truncate Claude response to keep within Cohere's 2048 character limit
        max_response_length = 1000  # Leave room for other text
        if len(claude_response) > max_response_length:
            claude_response = claude_response[:max_response_length] + "... [truncated]"
        
        description = f"""
        Network Security Guidance Analysis:
        Source IP: {source_ip}
        Risk Score: {risk_score}/100
        Threats Detected: {', '.join(threats) if threats else 'None detected'}
        Current Recommendations: {', '.join(recommendations) if recommendations else 'None'}
        
        Claude AI Guidance Summary:
        {claude_response}
        
        Analysis Context:
        This guidance was generated for a network security incident with risk score {risk_score}.
        The response provides actionable recommendations for addressing the identified threats.
        """
        
        # Ensure the final description doesn't exceed 2048 characters
        description = description.strip()
        if len(description) > 2048:
            # Truncate the description while keeping essential information
            essential_info = f"Network Security Guidance: IP {source_ip}, Risk {risk_score}/100, Threats: {', '.join(threats[:3]) if threats else 'None'}"
            remaining_chars = 2048 - len(essential_info) - 50  # Leave buffer
            if remaining_chars > 0:
                truncated_response = claude_response[:remaining_chars] + "... [truncated]"
                description = f"{essential_info}. Guidance: {truncated_response}"
            else:
                description = essential_info
        
        return description 