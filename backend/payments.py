import stripe, os, uuid
stripe.api_key = os.getenv("STRIPE_KEY")

def create_checkout(amount, user_id):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Bot Credits"},
                "unit_amount": int(amount * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="https://your-site/success",
        cancel_url="https://your-site/cancel",
        client_reference_id=str(user_id),
    )
    return session.url
