"""
AI Receptionist Booking System
Handles appointment scheduling, rescheduling, and cancellations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class ServiceType(Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    CHECKUP = "checkup"
    MEETING = "meeting"
    DEMO = "demo"

@dataclass
class TimeSlot:
    start_time: datetime
    end_time: datetime
    available: bool = True
    booked_by: Optional[str] = None

@dataclass
class Service:
    id: str
    name: str
    type: ServiceType
    duration_minutes: int
    price: float
    description: str
    requirements: List[str] = field(default_factory=list)

@dataclass
class Booking:
    id: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    service_id: str
    service_name: str
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    reminder_sent: bool = False
    confirmation_sent: bool = False

@dataclass
class BusinessHours:
    day_of_week: int  # 0=Monday, 6=Sunday
    open_time: time
    close_time: time
    is_open: bool = True
    breaks: List[tuple] = field(default_factory=list)  # [(start, end), ...]

class BookingSystem:
    def __init__(self):
        self.bookings: Dict[str, Booking] = {}
        self.services: Dict[str, Service] = {}
        self.business_hours: Dict[int, BusinessHours] = {}
        self.time_slots: Dict[str, List[TimeSlot]] = {}  # date_str -> slots
        
        # Initialize default services
        self._init_default_services()
        
        # Initialize default business hours (Mon-Fri 9-6, Sat 10-4)
        self._init_default_hours()
    
    def _init_default_services(self):
        """Initialize default services for various industries"""
        default_services = [
            Service(
                id="consultation_30",
                name="30-Minute Consultation",
                type=ServiceType.CONSULTATION,
                duration_minutes=30,
                price=0,
                description="Initial consultation to understand your needs"
            ),
            Service(
                id="consultation_60",
                name="1-Hour Deep Dive",
                type=ServiceType.CONSULTATION,
                duration_minutes=60,
                price=100,
                description="Detailed consultation with comprehensive analysis"
            ),
            Service(
                id="follow_up",
                name="Follow-up Session",
                type=ServiceType.FOLLOW_UP,
                duration_minutes=30,
                price=50,
                description="Follow-up on previous consultation"
            ),
            Service(
                id="emergency",
                name="Emergency Consultation",
                type=ServiceType.EMERGENCY,
                duration_minutes=45,
                price=200,
                description="Priority emergency consultation",
                requirements=["priority_handling", "immediate_response"]
            ),
            Service(
                id="demo_call",
                name="Product Demo",
                type=ServiceType.DEMO,
                duration_minutes=45,
                price=0,
                description="Live demonstration of our AI receptionist"
            ),
        ]
        
        for service in default_services:
            self.services[service.id] = service
    
    def _init_default_hours(self):
        """Initialize default business hours"""
        # Monday - Friday: 9:00 AM - 6:00 PM
        for day in range(5):
            self.business_hours[day] = BusinessHours(
                day_of_week=day,
                open_time=time(9, 0),
                close_time=time(18, 0),
                breaks=[(time(12, 0), time(13, 0))]  # Lunch break
            )
        
        # Saturday: 10:00 AM - 4:00 PM
        self.business_hours[5] = BusinessHours(
            day_of_week=5,
            open_time=time(10, 0),
            close_time=time(16, 0)
        )
        
        # Sunday: Closed
        self.business_hours[6] = BusinessHours(
            day_of_week=6,
            open_time=time(0, 0),
            close_time=time(0, 0),
            is_open=False
        )
    
    def add_service(self, service: Service) -> str:
        """Add a new service"""
        self.services[service.id] = service
        return service.id
    
    def get_service(self, service_id: str) -> Optional[Service]:
        """Get service by ID"""
        return self.services.get(service_id)
    
    def list_services(self, service_type: Optional[ServiceType] = None) -> List[Service]:
        """List all services, optionally filtered by type"""
        services = list(self.services.values())
        if service_type:
            services = [s for s in services if s.type == service_type]
        return services
    
    def get_available_slots(
        self,
        date: datetime,
        service_id: str,
        duration_minutes: Optional[int] = None
    ) -> List[TimeSlot]:
        """Get available time slots for a date and service"""
        service = self.services.get(service_id)
        if not service:
            return []
        
        duration = duration_minutes or service.duration_minutes
        
        # Check if business is open on this day
        day_of_week = date.weekday()
        hours = self.business_hours.get(day_of_week)
        
        if not hours or not hours.is_open:
            return []
        
        # Generate time slots
        slots = []
        current_time = datetime.combine(date.date(), hours.open_time)
        end_time = datetime.combine(date.date(), hours.close_time)
        
        while current_time + timedelta(minutes=duration) <= end_time:
            slot_end = current_time + timedelta(minutes=duration)
            
            # Check if slot overlaps with breaks
            is_break = False
            for break_start, break_end in hours.breaks:
                break_start_dt = datetime.combine(date.date(), break_start)
                break_end_dt = datetime.combine(date.date(), break_end)
                
                if current_time < break_end_dt and slot_end > break_start_dt:
                    is_break = True
                    break
            
            if not is_break:
                # Check if slot is already booked
                is_available = not any(
                    b.start_time < slot_end and b.end_time > current_time
                    and b.status in [BookingStatus.CONFIRMED, BookingStatus.PENDING]
                    for b in self.bookings.values()
                )
                
                slots.append(TimeSlot(
                    start_time=current_time,
                    end_time=slot_end,
                    available=is_available
                ))
            
            # Move to next slot (30-minute intervals)
            current_time += timedelta(minutes=30)
        
        return slots
    
    def create_booking(
        self,
        customer_name: str,
        customer_phone: str,
        service_id: str,
        start_time: datetime,
        customer_email: Optional[str] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Create a new booking"""
        service = self.services.get(service_id)
        if not service:
            return {"error": "Service not found"}
        
        # Check if slot is available
        slots = self.get_available_slots(start_time, service_id)
        slot_available = any(
            s.start_time == start_time and s.available
            for s in slots
        )
        
        if not slot_available:
            return {"error": "Time slot not available"}
        
        # Create booking
        booking_id = f"BK_{uuid.uuid4().hex[:12]}"
        end_time = start_time + timedelta(minutes=service.duration_minutes)
        
        booking = Booking(
            id=booking_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            service_id=service_id,
            service_name=service.name,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.PENDING,
            notes=notes
        )
        
        self.bookings[booking_id] = booking
        
        return {
            "success": True,
            "booking_id": booking_id,
            "service": service.name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "status": booking.status.value
        }
    
    def confirm_booking(self, booking_id: str) -> Dict[str, Any]:
        """Confirm a pending booking"""
        booking = self.bookings.get(booking_id)
        if not booking:
            return {"error": "Booking not found"}
        
        if booking.status != BookingStatus.PENDING:
            return {"error": f"Cannot confirm booking with status: {booking.status.value}"}
        
        booking.status = BookingStatus.CONFIRMED
        booking.confirmation_sent = True
        booking.updated_at = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "booking_id": booking_id,
            "status": booking.status.value,
            "message": "Booking confirmed successfully"
        }
    
    def reschedule_booking(
        self,
        booking_id: str,
        new_start_time: datetime
    ) -> Dict[str, Any]:
        """Reschedule an existing booking"""
        booking = self.bookings.get(booking_id)
        if not booking:
            return {"error": "Booking not found"}
        
        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            return {"error": f"Cannot reschedule booking with status: {booking.status.value}"}
        
        service = self.services.get(booking.service_id)
        if not service:
            return {"error": "Service not found"}
        
        # Check if new slot is available
        slots = self.get_available_slots(new_start_time, booking.service_id)
        slot_available = any(
            s.start_time == new_start_time and s.available
            for s in slots
        )
        
        if not slot_available:
            return {"error": "New time slot not available"}
        
        # Update booking
        old_start = booking.start_time
        booking.start_time = new_start_time
        booking.end_time = new_start_time + timedelta(minutes=service.duration_minutes)
        booking.updated_at = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "booking_id": booking_id,
            "old_time": old_start.isoformat(),
            "new_time": new_start_time.isoformat(),
            "status": booking.status.value
        }
    
    def cancel_booking(self, booking_id: str, reason: str = "") -> Dict[str, Any]:
        """Cancel a booking"""
        booking = self.bookings.get(booking_id)
        if not booking:
            return {"error": "Booking not found"}
        
        if booking.status == BookingStatus.CANCELLED:
            return {"error": "Booking already cancelled"}
        
        booking.status = BookingStatus.CANCELLED
        booking.updated_at = datetime.utcnow().isoformat()
        booking.notes += f"\nCancellation reason: {reason}"
        
        return {
            "success": True,
            "booking_id": booking_id,
            "status": booking.status.value,
            "message": "Booking cancelled successfully"
        }
    
    def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Get booking by ID"""
        return self.bookings.get(booking_id)
    
    def list_bookings(
        self,
        customer_phone: Optional[str] = None,
        status: Optional[BookingStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Booking]:
        """List bookings with optional filters"""
        bookings = list(self.bookings.values())
        
        if customer_phone:
            bookings = [b for b in bookings if b.customer_phone == customer_phone]
        
        if status:
            bookings = [b for b in bookings if b.status == status]
        
        if date_from:
            bookings = [b for b in bookings if b.start_time >= date_from]
        
        if date_to:
            bookings = [b for b in bookings if b.start_time <= date_to]
        
        # Sort by start time
        bookings.sort(key=lambda b: b.start_time)
        
        return bookings[:limit]
    
    def get_upcoming_bookings(
        self,
        customer_phone: str,
        days: int = 7
    ) -> List[Booking]:
        """Get upcoming bookings for a customer"""
        now = datetime.utcnow()
        future = now + timedelta(days=days)
        
        return self.list_bookings(
            customer_phone=customer_phone,
            status=BookingStatus.CONFIRMED,
            date_from=now,
            date_to=future
        )
    
    def get_day_schedule(self, date: datetime) -> Dict[str, Any]:
        """Get full schedule for a specific day"""
        day_start = datetime.combine(date.date(), time.min)
        day_end = datetime.combine(date.date(), time.max)
        
        bookings = self.list_bookings(
            date_from=day_start,
            date_to=day_end,
            limit=100
        )
        
        hours = self.business_hours.get(date.weekday())
        
        return {
            "date": date.date().isoformat(),
            "day_of_week": date.strftime("%A"),
            "is_open": hours.is_open if hours else False,
            "business_hours": {
                "open": hours.open_time.strftime("%H:%M") if hours else None,
                "close": hours.close_time.strftime("%H:%M") if hours else None
            } if hours else None,
            "total_bookings": len(bookings),
            "bookings": [
                {
                    "id": b.id,
                    "customer": b.customer_name,
                    "service": b.service_name,
                    "start": b.start_time.strftime("%H:%M"),
                    "end": b.end_time.strftime("%H:%M"),
                    "status": b.status.value
                }
                for b in bookings
            ]
        }
    
    def update_business_hours(
        self,
        day_of_week: int,
        open_time: time,
        close_time: time,
        is_open: bool = True,
        breaks: Optional[List[tuple]] = None
    ):
        """Update business hours for a day"""
        self.business_hours[day_of_week] = BusinessHours(
            day_of_week=day_of_week,
            open_time=open_time,
            close_time=close_time,
            is_open=is_open,
            breaks=breaks or []
        )
    
    def get_booking_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get booking statistics"""
        since = datetime.utcnow() - timedelta(days=days)
        bookings = [b for b in self.bookings.values() if b.created_at and datetime.fromisoformat(b.created_at) >= since]
        
        total = len(bookings)
        confirmed = len([b for b in bookings if b.status == BookingStatus.CONFIRMED])
        cancelled = len([b for b in bookings if b.status == BookingStatus.CANCELLED])
        completed = len([b for b in bookings if b.status == BookingStatus.COMPLETED])
        
        # Calculate revenue
        revenue = sum(
            self.services.get(b.service_id, Service("", "", ServiceType.CONSULTATION, 0, 0, "")).price
            for b in bookings if b.status in [BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
        )
        
        return {
            "period_days": days,
            "total_bookings": total,
            "confirmed": confirmed,
            "cancelled": cancelled,
            "completed": completed,
            "confirmation_rate": round(confirmed / total * 100, 2) if total > 0 else 0,
            "cancellation_rate": round(cancelled / total * 100, 2) if total > 0 else 0,
            "estimated_revenue": revenue
        }


# Global booking system instance
booking_system = BookingSystem()


def get_booking_system() -> BookingSystem:
    """Get the global booking system instance"""
    return booking_system


async def test_booking_system():
    """Test the booking system"""
    bs = BookingSystem()
    
    # List services
    print("Available services:")
    for service in bs.list_services():
        print(f"  - {service.name} ({service.duration_minutes} min): ${service.price}")
    
    # Get available slots for tomorrow
    tomorrow = datetime.utcnow() + timedelta(days=1)
    print(f"\nAvailable slots for {tomorrow.date()}:")
    slots = bs.get_available_slots(tomorrow, "consultation_30")
    for slot in slots[:5]:  # Show first 5
        status = "Available" if slot.available else "Booked"
        print(f"  - {slot.start_time.strftime('%H:%M')}: {status}")
    
    # Create a booking
    print("\nCreating booking...")
    result = bs.create_booking(
        customer_name="John Doe",
        customer_phone="+919876543210",
        service_id="consultation_30",
        start_time=slots[0].start_time if slots else tomorrow.replace(hour=10, minute=0),
        customer_email="john@example.com"
    )
    print(f"Result: {json.dumps(result, indent=2)}")
    
    if result.get("success"):
        booking_id = result["booking_id"]
        
        # Confirm booking
        print("\nConfirming booking...")
        confirm_result = bs.confirm_booking(booking_id)
        print(f"Result: {json.dumps(confirm_result, indent=2)}")
        
        # Get booking details
        print("\nBooking details:")
        booking = bs.get_booking(booking_id)
        if booking:
            print(f"  ID: {booking.id}")
            print(f"  Customer: {booking.customer_name}")
            print(f"  Service: {booking.service_name}")
            print(f"  Time: {booking.start_time}")
            print(f"  Status: {booking.status.value}")
        
        # Get stats
        print("\nBooking stats:")
        stats = bs.get_booking_stats(days=30)
        print(f"  Total: {stats['total_bookings']}")
        print(f"  Confirmed: {stats['confirmed']}")
        print(f"  Confirmation rate: {stats['confirmation_rate']}%")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_booking_system())
