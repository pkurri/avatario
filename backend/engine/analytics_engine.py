"""
AI Receptionist Analytics Engine
Tracks metrics, generates reports, and provides insights
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio

class MetricType(Enum):
    CALL_VOLUME = "call_volume"
    CALL_DURATION = "call_duration"
    RESPONSE_TIME = "response_time"
    RESOLUTION_RATE = "resolution_rate"
    ESCALATION_RATE = "escalation_rate"
    SENTIMENT_SCORE = "sentiment_score"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    AI_CONFIDENCE = "ai_confidence"

class TimeGranularity(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

@dataclass
class MetricDataPoint:
    timestamp: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CallQualityScore:
    call_sid: str
    overall_score: float  # 0-100
    factors: Dict[str, float]  # Individual factor scores
    transcript_quality: float
    response_relevance: float
    user_satisfaction: float
    resolution_achieved: bool
    escalation_required: bool
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class SentimentAnalysis:
    call_sid: str
    overall_sentiment: str  # positive, negative, neutral
    sentiment_score: float  # -1.0 to 1.0
    emotions: Dict[str, float]  # joy, anger, sadness, fear, etc.
    key_phrases: List[str]
    turning_points: List[Dict]  # Moments where sentiment changed
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class ABTestVariant:
    variant_id: str
    name: str
    description: str
    config: Dict[str, Any]
    traffic_percentage: float

@dataclass
class ABTest:
    test_id: str
    name: str
    hypothesis: str
    variants: List[ABTestVariant]
    start_date: str
    end_date: Optional[str]
    status: str  # running, completed, paused
    metrics: List[str]  # Metrics to track
    results: Dict[str, Any] = field(default_factory=dict)

class AnalyticsEngine:
    def __init__(self):
        self.metrics: Dict[MetricType, List[MetricDataPoint]] = {
            metric: [] for metric in MetricType
        }
        self.call_quality_scores: Dict[str, CallQualityScore] = {}
        self.sentiment_analyses: Dict[str, SentimentAnalysis] = {}
        self.ab_tests: Dict[str, ABTest] = {}
        
        # Performance thresholds
        self.thresholds = {
            "max_response_time": 3.0,  # seconds
            "min_sentiment": -0.3,
            "max_escalation_rate": 0.2,
            "min_resolution_rate": 0.8
        }
    
    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        metadata: Optional[Dict] = None
    ):
        """Record a metric data point"""
        point = MetricDataPoint(
            timestamp=datetime.utcnow().isoformat(),
            value=value,
            metadata=metadata or {}
        )
        self.metrics[metric_type].append(point)
    
    def get_metrics_summary(
        self,
        metric_type: MetricType,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        points = [
            p for p in self.metrics[metric_type]
            if datetime.fromisoformat(p.timestamp) >= cutoff
        ]
        
        if not points:
            return {"count": 0, "average": 0, "min": 0, "max": 0}
        
        values = [p.value for p in points]
        
        return {
            "count": len(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else 0,
            "trend": "up" if len(values) > 1 and values[-1] > values[0] else "down"
        }
    
    def get_time_series(
        self,
        metric_type: MetricType,
        granularity: TimeGranularity,
        hours: int = 24
    ) -> List[Dict]:
        """Get time series data for a metric"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        points = [
            p for p in self.metrics[metric_type]
            if datetime.fromisoformat(p.timestamp) >= cutoff
        ]
        
        # Group by granularity
        grouped = {}
        for point in points:
            dt = datetime.fromisoformat(point.timestamp)
            
            if granularity == TimeGranularity.HOURLY:
                key = dt.strftime("%Y-%m-%d %H:00")
            elif granularity == TimeGranularity.DAILY:
                key = dt.strftime("%Y-%m-%d")
            elif granularity == TimeGranularity.WEEKLY:
                key = dt.strftime("%Y-W%U")
            else:  # MONTHLY
                key = dt.strftime("%Y-%m")
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(point.value)
        
        # Calculate averages
        result = []
        for key, values in sorted(grouped.items()):
            result.append({
                "timestamp": key,
                "value": sum(values) / len(values),
                "count": len(values)
            })
        
        return result
    
    def analyze_sentiment(
        self,
        call_sid: str,
        transcript: List[Dict[str, str]]
    ) -> SentimentAnalysis:
        """Analyze sentiment from call transcript"""
        # TODO: Integrate with sentiment analysis model (e.g., AWS Comprehend, OpenAI)
        
        # Simple keyword-based analysis for now
        positive_words = ["good", "great", "excellent", "happy", "satisfied", "thank", "perfect"]
        negative_words = ["bad", "terrible", "angry", "frustrated", "disappointed", "problem", "issue"]
        
        positive_count = 0
        negative_count = 0
        
        all_text = " ".join([t.get("text", "").lower() for t in transcript])
        
        for word in positive_words:
            positive_count += all_text.count(word)
        
        for word in negative_words:
            negative_count += all_text.count(word)
        
        total = positive_count + negative_count
        
        if total == 0:
            sentiment_score = 0.0
            overall_sentiment = "neutral"
        else:
            sentiment_score = (positive_count - negative_count) / total
            if sentiment_score > 0.2:
                overall_sentiment = "positive"
            elif sentiment_score < -0.2:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
        
        analysis = SentimentAnalysis(
            call_sid=call_sid,
            overall_sentiment=overall_sentiment,
            sentiment_score=sentiment_score,
            emotions={
                "joy": max(0, sentiment_score),
                "anger": max(0, -sentiment_score),
                "sadness": 0.0,
                "fear": 0.0,
                "neutral": 1.0 - abs(sentiment_score)
            },
            key_phrases=[],  # TODO: Extract key phrases
            turning_points=[]  # TODO: Detect sentiment changes
        )
        
        self.sentiment_analyses[call_sid] = analysis
        
        # Record metric
        self.record_metric(
            MetricType.SENTIMENT_SCORE,
            sentiment_score,
            {"call_sid": call_sid}
        )
        
        return analysis
    
    def score_call_quality(
        self,
        call_sid: str,
        transcript: List[Dict],
        resolution_achieved: bool,
        escalation_required: bool,
        duration_seconds: int
    ) -> CallQualityScore:
        """Score the quality of a call"""
        # Calculate individual factors
        
        # 1. Transcript quality (based on message count and length)
        transcript_quality = min(100, len(transcript) * 10)
        
        # 2. Response relevance (based on AI response length and context)
        ai_messages = [t for t in transcript if t.get("role") == "assistant"]
        avg_response_length = sum(len(t.get("text", "")) for t in ai_messages) / len(ai_messages) if ai_messages else 0
        response_relevance = min(100, avg_response_length / 2)
        
        # 3. User satisfaction (based on sentiment)
        sentiment = self.sentiment_analyses.get(call_sid)
        user_satisfaction = (sentiment.sentiment_score + 1) * 50 if sentiment else 50
        
        # 4. Resolution rate
        resolution_score = 100 if resolution_achieved else 0
        
        # 5. Escalation penalty
        escalation_penalty = -20 if escalation_required else 0
        
        # Calculate overall score
        factors = {
            "transcript_quality": transcript_quality,
            "response_relevance": response_relevance,
            "user_satisfaction": user_satisfaction,
            "resolution_score": resolution_score,
            "escalation_penalty": escalation_penalty
        }
        
        overall_score = sum(factors.values()) / len(factors)
        overall_score = max(0, min(100, overall_score))
        
        score = CallQualityScore(
            call_sid=call_sid,
            overall_score=overall_score,
            factors=factors,
            transcript_quality=transcript_quality,
            response_relevance=response_relevance,
            user_satisfaction=user_satisfaction,
            resolution_achieved=resolution_achieved,
            escalation_required=escalation_required
        )
        
        self.call_quality_scores[call_sid] = score
        
        # Record metrics
        self.record_metric(
            MetricType.CUSTOMER_SATISFACTION,
            user_satisfaction,
            {"call_sid": call_sid}
        )
        
        return score
    
    def get_quality_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of call quality scores"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        scores = [
            s for s in self.call_quality_scores.values()
            if datetime.fromisoformat(s.timestamp) >= cutoff
        ]
        
        if not scores:
            return {"count": 0, "average_score": 0}
        
        overall_scores = [s.overall_score for s in scores]
        
        return {
            "count": len(scores),
            "average_score": sum(overall_scores) / len(overall_scores),
            "min_score": min(overall_scores),
            "max_score": max(overall_scores),
            "resolution_rate": sum(1 for s in scores if s.resolution_achieved) / len(scores),
            "escalation_rate": sum(1 for s in scores if s.escalation_required) / len(scores),
            "scores": [
                {
                    "call_sid": s.call_sid,
                    "score": s.overall_score,
                    "factors": s.factors
                }
                for s in scores[-10:]  # Last 10
            ]
        }
    
    def create_ab_test(
        self,
        name: str,
        hypothesis: str,
        variants: List[Dict],
        metrics: List[str],
        duration_days: int = 14
    ) -> str:
        """Create a new A/B test"""
        test_id = f"AB_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        ab_variants = []
        for i, v in enumerate(variants):
            ab_variants.append(ABTestVariant(
                variant_id=f"{test_id}_v{i}",
                name=v.get("name", f"Variant {i}"),
                description=v.get("description", ""),
                config=v.get("config", {}),
                traffic_percentage=v.get("traffic_percentage", 100 / len(variants))
            ))
        
        test = ABTest(
            test_id=test_id,
            name=name,
            hypothesis=hypothesis,
            variants=ab_variants,
            start_date=datetime.utcnow().isoformat(),
            end_date=(datetime.utcnow() + timedelta(days=duration_days)).isoformat(),
            status="running",
            metrics=metrics
        )
        
        self.ab_tests[test_id] = test
        return test_id
    
    def get_ab_test_variant(self, test_id: str, user_id: str) -> Optional[ABTestVariant]:
        """Get variant assignment for a user"""
        test = self.ab_tests.get(test_id)
        if not test or test.status != "running":
            return None
        
        # Simple hash-based assignment
        hash_val = hash(f"{test_id}_{user_id}") % 100
        cumulative = 0
        
        for variant in test.variants:
            cumulative += variant.traffic_percentage
            if hash_val < cumulative:
                return variant
        
        return test.variants[-1] if test.variants else None
    
    def record_ab_test_metric(
        self,
        test_id: str,
        variant_id: str,
        metric_name: str,
        value: float
    ):
        """Record a metric for an A/B test variant"""
        test = self.ab_tests.get(test_id)
        if not test:
            return
        
        if "variant_metrics" not in test.results:
            test.results["variant_metrics"] = {}
        
        if variant_id not in test.results["variant_metrics"]:
            test.results["variant_metrics"][variant_id] = {}
        
        if metric_name not in test.results["variant_metrics"][variant_id]:
            test.results["variant_metrics"][variant_id][metric_name] = []
        
        test.results["variant_metrics"][variant_id][metric_name].append({
            "timestamp": datetime.utcnow().isoformat(),
            "value": value
        })
    
    def get_ab_test_results(self, test_id: str) -> Optional[Dict]:
        """Get results for an A/B test"""
        test = self.ab_tests.get(test_id)
        if not test:
            return None
        
        return {
            "test_id": test.test_id,
            "name": test.name,
            "hypothesis": test.hypothesis,
            "status": test.status,
            "start_date": test.start_date,
            "end_date": test.end_date,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "name": v.name,
                    "traffic_percentage": v.traffic_percentage,
                    "metrics": test.results.get("variant_metrics", {}).get(v.variant_id, {})
                }
                for v in test.variants
            ]
        }
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for analytics dashboard"""
        now = datetime.utcnow()
        
        return {
            "timestamp": now.isoformat(),
            "summary": {
                "calls_last_24h": self.get_metrics_summary(MetricType.CALL_VOLUME, 24),
                "avg_response_time": self.get_metrics_summary(MetricType.RESPONSE_TIME, 24),
                "escalation_rate": self.get_metrics_summary(MetricType.ESCALATION_RATE, 24),
                "avg_sentiment": self.get_metrics_summary(MetricType.SENTIMENT_SCORE, 24),
                "quality_score": self.get_quality_summary(24)
            },
            "time_series": {
                "call_volume": self.get_time_series(MetricType.CALL_VOLUME, TimeGranularity.HOURLY, 24),
                "sentiment": self.get_time_series(MetricType.SENTIMENT_SCORE, TimeGranularity.HOURLY, 24)
            },
            "alerts": self._generate_alerts(),
            "active_ab_tests": [
                {"test_id": t.test_id, "name": t.name, "status": t.status}
                for t in self.ab_tests.values()
                if t.status == "running"
            ]
        }
    
    def _generate_alerts(self) -> List[Dict]:
        """Generate alerts based on metrics"""
        alerts = []
        
        # Check escalation rate
        escalation_summary = self.get_metrics_summary(MetricType.ESCALATION_RATE, 1)
        if escalation_summary["average"] > self.thresholds["max_escalation_rate"]:
            alerts.append({
                "severity": "warning",
                "type": "high_escalation_rate",
                "message": f"Escalation rate ({escalation_summary['average']:.1%}) exceeds threshold",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check response time
        response_summary = self.get_metrics_summary(MetricType.RESPONSE_TIME, 1)
        if response_summary["average"] > self.thresholds["max_response_time"]:
            alerts.append({
                "severity": "warning",
                "type": "slow_response",
                "message": f"Average response time ({response_summary['average']:.1f}s) exceeds threshold",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check sentiment
        sentiment_summary = self.get_metrics_summary(MetricType.SENTIMENT_SCORE, 1)
        if sentiment_summary["average"] < self.thresholds["min_sentiment"]:
            alerts.append({
                "severity": "critical",
                "type": "low_sentiment",
                "message": f"Average sentiment ({sentiment_summary['average']:.2f}) is below threshold",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return alerts


# Global analytics engine instance
analytics_engine = AnalyticsEngine()


def get_analytics_engine() -> AnalyticsEngine:
    """Get the global analytics engine instance"""
    return analytics_engine


async def test_analytics_engine():
    """Test the analytics engine"""
    engine = AnalyticsEngine()
    
    # Record some metrics
    print("Recording metrics...")
    for i in range(10):
        engine.record_metric(MetricType.CALL_VOLUME, float(i + 1))
        engine.record_metric(MetricType.SENTIMENT_SCORE, 0.5 + (i * 0.05))
    
    # Get summary
    print("\nCall Volume Summary (24h):")
    summary = engine.get_metrics_summary(MetricType.CALL_VOLUME, 24)
    print(f"  Count: {summary['count']}")
    print(f"  Average: {summary['average']:.2f}")
    print(f"  Trend: {summary['trend']}")
    
    # Get time series
    print("\nTime Series (Hourly):")
    ts = engine.get_time_series(MetricType.CALL_VOLUME, TimeGranularity.HOURLY, 24)
    for point in ts[:5]:
        print(f"  {point['timestamp']}: {point['value']:.2f}")
    
    # Test sentiment analysis
    print("\nSentiment Analysis:")
    transcript = [
        {"role": "user", "text": "I'm having a problem with my account"},
        {"role": "assistant", "text": "I'd be happy to help you with that"},
        {"role": "user", "text": "Thank you, that would be great"}
    ]
    sentiment = engine.analyze_sentiment("CALL_001", transcript)
    print(f"  Overall: {sentiment.overall_sentiment}")
    print(f"  Score: {sentiment.sentiment_score:.2f}")
    
    # Test call quality scoring
    print("\nCall Quality Score:")
    score = engine.score_call_quality("CALL_001", transcript, True, False, 120)
    print(f"  Overall: {score.overall_score:.1f}/100")
    print(f"  Factors: {score.factors}")
    
    # Generate dashboard
    print("\nDashboard Data:")
    dashboard = engine.generate_dashboard_data()
    print(f"  Alerts: {len(dashboard['alerts'])}")
    print(f"  Time series points: {len(dashboard['time_series']['call_volume'])}")


if __name__ == "__main__":
    asyncio.run(test_analytics_engine())
