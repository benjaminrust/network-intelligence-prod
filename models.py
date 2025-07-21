import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url):
        self.database_url = database_url
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            with conn.cursor() as cur:
                # Security Events Table with vector support
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS security_events (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        event_type VARCHAR(100) NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        source_ip INET,
                        destination_ip INET,
                        source_port INTEGER,
                        destination_port INTEGER,
                        protocol VARCHAR(10),
                        payload_size INTEGER,
                        user_agent TEXT,
                        country_code VARCHAR(3),
                        city VARCHAR(100),
                        latitude DECIMAL(10, 8),
                        longitude DECIMAL(11, 8),
                        risk_score INTEGER DEFAULT 0,
                        threat_indicators JSONB,
                        metadata JSONB,
                        status VARCHAR(20) DEFAULT 'active',
                        embedding vector(1024),
                        text_description TEXT
                    )
                """)
                
                # Network Analytics Table with vector support
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS network_analytics (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value DECIMAL(15, 2) NOT NULL,
                        metric_unit VARCHAR(20),
                        source VARCHAR(100),
                        tags JSONB,
                        period VARCHAR(20) DEFAULT 'realtime',
                        embedding vector(1024),
                        text_description TEXT
                    )
                """)
                
                # New Traffic Analysis Embeddings Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS traffic_embeddings (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        analysis_type VARCHAR(100) NOT NULL,
                        source_data JSONB NOT NULL,
                        text_description TEXT NOT NULL,
                        embedding vector(1024) NOT NULL,
                        risk_score INTEGER DEFAULT 0,
                        similarity_threshold DECIMAL(5, 4) DEFAULT 0.8,
                        metadata JSONB,
                        status VARCHAR(20) DEFAULT 'active'
                    )
                """)
                
                # New Claude Guidance Responses Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS claude_guidance_responses (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        request_id VARCHAR(255) UNIQUE NOT NULL,
                        source_ip VARCHAR(45),
                        risk_score INTEGER DEFAULT 0,
                        threats_detected JSONB,
                        recommendations JSONB,
                        claude_response TEXT NOT NULL,
                        embedding vector(1024) NOT NULL,
                        model_used VARCHAR(100) DEFAULT 'claude-3-5-sonnet-20241022',
                        response_tokens INTEGER,
                        processing_time_ms INTEGER,
                        metadata JSONB,
                        status VARCHAR(20) DEFAULT 'active'
                    )
                """)
                
                # Threat Intelligence Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS threat_intelligence (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        indicator_type VARCHAR(50) NOT NULL,
                        indicator_value TEXT NOT NULL,
                        confidence_level VARCHAR(20) DEFAULT 'medium',
                        threat_category VARCHAR(100),
                        description TEXT,
                        source VARCHAR(100),
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE,
                        metadata JSONB
                    )
                """)
                
                # User Sessions Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255) UNIQUE NOT NULL,
                        user_id VARCHAR(100),
                        ip_address INET,
                        user_agent TEXT,
                        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        logout_time TIMESTAMP,
                        session_duration INTEGER,
                        status VARCHAR(20) DEFAULT 'active',
                        location_data JSONB,
                        risk_factors JSONB
                    )
                """)
                
                # Network Topology Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS network_topology (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        node_id VARCHAR(100) NOT NULL,
                        node_type VARCHAR(50) NOT NULL,
                        node_name VARCHAR(255),
                        ip_address INET,
                        mac_address VARCHAR(17),
                        status VARCHAR(20) DEFAULT 'active',
                        connections JSONB,
                        metadata JSONB
                    )
                """)
                
                # Create indexes for better performance
                cur.execute("CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_security_events_source_ip ON security_events(source_ip)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_threat_intelligence_value ON threat_intelligence(indicator_value)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_threat_intelligence_active ON threat_intelligence(active)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_network_analytics_timestamp ON network_analytics(timestamp)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id)")
                
                # Create vector indexes for similarity search
                cur.execute("CREATE INDEX IF NOT EXISTS idx_security_events_embedding ON security_events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_network_analytics_embedding ON network_analytics USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_traffic_embeddings_embedding ON traffic_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_claude_guidance_embedding ON claude_guidance_responses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
                
            conn.commit()
            logger.info("Database tables initialized successfully with vector support")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            conn.rollback()
        finally:
            conn.close()

class SecurityEvent:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_event(self, event_data):
        """Create a new security event"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO security_events (
                        event_type, severity, source_ip, destination_ip, 
                        source_port, destination_port, protocol, payload_size,
                        user_agent, country_code, city, latitude, longitude,
                        risk_score, threat_indicators, metadata, embedding, text_description
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING *
                """, (
                    event_data.get('event_type'),
                    event_data.get('severity', 'medium'),
                    event_data.get('source_ip'),
                    event_data.get('destination_ip'),
                    event_data.get('source_port'),
                    event_data.get('destination_port'),
                    event_data.get('protocol'),
                    event_data.get('payload_size'),
                    event_data.get('user_agent'),
                    event_data.get('country_code'),
                    event_data.get('city'),
                    event_data.get('latitude'),
                    event_data.get('longitude'),
                    event_data.get('risk_score', 0),
                    json.dumps(event_data.get('threat_indicators', [])),
                    json.dumps(event_data.get('metadata', {})),
                    event_data.get('embedding'),
                    event_data.get('text_description')
                ))
                
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error creating security event: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_events(self, limit=100, offset=0, filters=None):
        """Get security events with optional filtering"""
        conn = self.db_manager.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM security_events WHERE 1=1"
                params = []
                
                if filters:
                    if filters.get('severity'):
                        query += " AND severity = %s"
                        params.append(filters['severity'])
                    
                    if filters.get('source_ip'):
                        query += " AND source_ip = %s"
                        params.append(filters['source_ip'])
                    
                    if filters.get('event_type'):
                        query += " AND event_type = %s"
                        params.append(filters['event_type'])
                    
                    if filters.get('status'):
                        query += " AND status = %s"
                        params.append(filters['status'])
                
                query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error getting security events: {e}")
            return []
        finally:
            conn.close()

class NetworkAnalytics:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def record_metric(self, metric_data):
        """Record a network metric"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO network_analytics (
                        metric_name, metric_value, metric_unit, source, tags, period, embedding, text_description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
                """, (
                    metric_data.get('metric_name'),
                    metric_data.get('metric_value'),
                    metric_data.get('metric_unit'),
                    metric_data.get('source'),
                    json.dumps(metric_data.get('tags', {})),
                    metric_data.get('period', 'realtime'),
                    metric_data.get('embedding'),
                    metric_data.get('text_description')
                ))
                
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error recording metric: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_metrics(self, metric_name=None, period='realtime', limit=100):
        """Get network metrics"""
        conn = self.db_manager.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM network_analytics WHERE 1=1"
                params = []
                
                if metric_name:
                    query += " AND metric_name = %s"
                    params.append(metric_name)
                
                if period:
                    query += " AND period = %s"
                    params.append(period)
                
                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return []
        finally:
            conn.close()

class ThreatIntelligence:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def add_indicator(self, indicator_data):
        """Add a new threat indicator"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO threat_intelligence (
                        indicator_type, indicator_value, confidence_level,
                        threat_category, description, source, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *
                """, (
                    indicator_data.get('indicator_type'),
                    indicator_data.get('indicator_value'),
                    indicator_data.get('confidence_level', 'medium'),
                    indicator_data.get('threat_category'),
                    indicator_data.get('description'),
                    indicator_data.get('source'),
                    json.dumps(indicator_data.get('metadata', {}))
                ))
                
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error adding threat indicator: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def check_indicator(self, indicator_value, indicator_type=None):
        """Check if an indicator exists in threat intelligence"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM threat_intelligence WHERE indicator_value = %s AND active = TRUE"
                params = [indicator_value]
                
                if indicator_type:
                    query += " AND indicator_type = %s"
                    params.append(indicator_type)
                
                cur.execute(query, params)
                result = cur.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error checking indicator: {e}")
            return None
        finally:
            conn.close()

class UserSession:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_session(self, session_data):
        """Create a new user session"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO user_sessions (
                        session_id, user_id, ip_address, user_agent,
                        location_data, risk_factors
                    ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *
                """, (
                    session_data.get('session_id'),
                    session_data.get('user_id'),
                    session_data.get('ip_address'),
                    session_data.get('user_agent'),
                    json.dumps(session_data.get('location_data', {})),
                    json.dumps(session_data.get('risk_factors', {}))
                ))
                
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def update_session_activity(self, session_id):
        """Update session last activity"""
        conn = self.db_manager.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_sessions 
                    SET last_activity = CURRENT_TIMESTAMP 
                    WHERE session_id = %s
                """, (session_id,))
                
                conn.commit()
                return cur.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            conn.rollback()
            return False
        finally:
            conn.close() 

class TrafficEmbeddings:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def store_embedding(self, embedding_data):
        """Store a traffic analysis embedding"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO traffic_embeddings (
                        analysis_type, source_data, text_description, embedding,
                        risk_score, similarity_threshold, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *
                """, (
                    embedding_data.get('analysis_type'),
                    json.dumps(embedding_data.get('source_data', {})),
                    embedding_data.get('text_description'),
                    embedding_data.get('embedding'),
                    embedding_data.get('risk_score', 0),
                    embedding_data.get('similarity_threshold', 0.8),
                    json.dumps(embedding_data.get('metadata', {}))
                ))
                
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def find_similar_patterns(self, query_embedding, analysis_type=None, limit=10, similarity_threshold=0.8):
        """Find similar traffic patterns using vector similarity"""
        conn = self.db_manager.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT *, 
                           (1 - (embedding <=> %s)) as similarity_score
                    FROM traffic_embeddings 
                    WHERE (1 - (embedding <=> %s)) >= %s
                """
                params = [query_embedding, query_embedding, similarity_threshold]
                
                if analysis_type:
                    query += " AND analysis_type = %s"
                    params.append(analysis_type)
                
                query += " ORDER BY embedding <=> %s LIMIT %s"
                params.extend([query_embedding, limit])
                
                cur.execute(query, params)
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error finding similar patterns: {e}")
            return []
        finally:
            conn.close()
    
    def get_embeddings_by_type(self, analysis_type, limit=100):
        """Get embeddings by analysis type"""
        conn = self.db_manager.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM traffic_embeddings 
                    WHERE analysis_type = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (analysis_type, limit))
                
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error getting embeddings by type: {e}")
            return []
        finally:
            conn.close()
    
    def update_embedding_metadata(self, embedding_id, metadata):
        """Update embedding metadata"""
        conn = self.db_manager.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE traffic_embeddings 
                    SET metadata = %s 
                    WHERE id = %s
                """, (json.dumps(metadata), embedding_id))
                
                conn.commit()
                return cur.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating embedding metadata: {e}")
            conn.rollback()
            return False
        finally:
            conn.close() 

class ClaudeGuidanceResponse:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def store_guidance_response(self, guidance_data):
        """Store a Claude guidance response with embedding"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO claude_guidance_responses (
                        request_id, source_ip, risk_score, threats_detected, recommendations,
                        claude_response, embedding, model_used, response_tokens, 
                        processing_time_ms, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
                """, (
                    guidance_data.get('request_id'),
                    guidance_data.get('source_ip'),
                    guidance_data.get('risk_score', 0),
                    json.dumps(guidance_data.get('threats_detected', [])),
                    json.dumps(guidance_data.get('recommendations', [])),
                    guidance_data.get('claude_response'),
                    guidance_data.get('embedding'),
                    guidance_data.get('model_used', 'claude-3-5-sonnet-20241022'),
                    guidance_data.get('response_tokens'),
                    guidance_data.get('processing_time_ms'),
                    json.dumps(guidance_data.get('metadata', {}))
                ))
                
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error storing guidance response: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def find_similar_guidance(self, query_embedding, limit=5, similarity_threshold=0.8):
        """Find similar guidance responses using vector similarity"""
        conn = self.db_manager.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT *, 
                           (1 - (embedding <=> %s)) as similarity_score
                    FROM claude_guidance_responses 
                    WHERE (1 - (embedding <=> %s)) >= %s AND status = 'active'
                """
                params = [query_embedding, query_embedding, similarity_threshold]
                
                query += " ORDER BY embedding <=> %s LIMIT %s"
                params.extend([query_embedding, limit])
                
                cur.execute(query, params)
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error finding similar guidance: {e}")
            return []
        finally:
            conn.close()
    
    def get_guidance_by_risk_score(self, risk_score, limit=10):
        """Get guidance responses by risk score range"""
        conn = self.db_manager.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get responses within ±10 points of the risk score
                cur.execute("""
                    SELECT * FROM claude_guidance_responses 
                    WHERE risk_score BETWEEN %s AND %s AND status = 'active'
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (max(0, risk_score - 10), min(100, risk_score + 10), limit))
                
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error getting guidance by risk score: {e}")
            return []
        finally:
            conn.close()
    
    def get_recent_guidance(self, hours=24, limit=20):
        """Get recent guidance responses"""
        conn = self.db_manager.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM claude_guidance_responses 
                    WHERE timestamp >= NOW() - INTERVAL '%s hours' AND status = 'active'
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (hours, limit))
                
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error getting recent guidance: {e}")
            return []
        finally:
            conn.close() 