import random

def get_stripe_status(customer_email: str):
    """Simulates checking Stripe payment history."""
    # Mock database of payments
    payments = {
        "operatordef978@gmail.com": {"status": "Succeeded", "last_amount": "$99.00", "date": "2024-02-15"},
        "bob@example.com": {"status": "Failed", "last_amount": "$29.00", "date": "2024-03-01"},
        "charlie@example.com": {"status": "Pending", "last_amount": "$49.00", "date": "2024-03-02"},
    }
    
    return payments.get(customer_email.lower(), {"status": "No record found", "message": "Customer doesn't have a Stripe history."})

def get_shopify_order(order_id: str):
    """Simulates checking Shopify order/shipping status."""
    statuses = ["In Transit", "Delivered", "Processing", "Shipped"]
    tracking_nums = ["TRK8822910", "TRK1102933", "TRK9920112", "TRK5566778"]
    
    # Deterministic mock based on order_id
    idx = hash(order_id) % len(statuses)
    
    return {
        "order_id": order_id,
        "status": statuses[idx],
        "tracking_number": tracking_nums[idx],
        "estimated_delivery": "2024-03-05"
    }

def schedule_calendar_event(title: str, date_time: str):
    """Simulates scheduling a meeting in Google Calendar."""
    # In a real app, this would use google-api-python-client
    return {
        "status": "Confirmed",
        "event": title,
        "time": date_time,
        "link": f"https://meet.google.com/mock-{random.randint(100, 999)}"
    }
