from flask import Flask, jsonify, request, Response
import stripe

app = Flask(__name__)

# Use a test secret key from Stripe for demo purposes
stripe.api_key = 'sk_test_51Of6goKZ0oo6AUWAhVAGBbJgiaBVpVUkPLBQOdVE4RKnE38lsscMVc85p2j0s6EjAD0bBOxz4pUIAh13t3UwWiTe00kHiko9gx'

# Your endpoint secret from Stripe dashboard
endpoint_secret = 'whsec_qx2ZzgwYuBaTXkYIUaWZeek6H4MroVqb'

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', 'https://try-design-team.webflow.io/')
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    return response

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.get_json()
    service_name = data.get('serviceName')
    quantity = data.get('quantity')
    subtotal = data.get('subtotal')
    purchase_type = data.get('purchaseType')
    min_order = data.get('minOrder')
    unit_type = data.get('unitType')
    additional_fee = data.get('additionalFee', 0)  # Additional fee if any
    customer_email = data.get('customer_email')  # Get customer email if available

    try:
        if purchase_type == "one-time":
            # Create a Stripe Checkout session for one-time purchase
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': service_name,
                            },
                            'unit_amount': subtotal // quantity,
                        },
                        'quantity': quantity,
                    }
                ],
                mode='payment',
                customer_email=customer_email,  # Include customer email
                success_url="https://try-design-team.webflow.io/payment-success",
                cancel_url=data['cancel_url'],
                allow_promotion_codes=True  # Add this line to allow promotion codes
            )
        elif purchase_type == "membership":
            # Create a Stripe product for the membership
            product = stripe.Product.create(
                name="Designteam Membership",
                description=f"Enjoy discounts on all orders and a $500 credit per month for any design with our membership. Get your first {service_name} (up to {min_order} {unit_type}) free on us!"
            )

            # Create a Stripe price for the membership
            price = stripe.Price.create(
                unit_amount=50000,  # $500 in cents
                currency="usd",
                recurring={"interval": "month"},
                product=product.id,
            )

            # Create line items for the session
            line_items = [
                {
                    'price': price.id,
                    'quantity': 1,
                }
            ]

            # If there's an additional fee, add it as a one-time charge
            if additional_fee > 0:
                additional_units = quantity - min_order
                line_items.append(
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"{service_name}",
                                'description': f"{additional_units} {unit_type}",
                            },
                            'unit_amount': additional_fee,
                        },
                        'quantity': 1,
                    }
                )

            # Create a Stripe Checkout session for membership
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='subscription',
                customer_email=customer_email,  # Include customer email
                success_url="https://try-design-team.webflow.io/membership-success",
                cancel_url=data['cancel_url'],
                allow_promotion_codes=True  # Add this line to allow promotion codes
            )
        else:
            return jsonify(error="Invalid purchase type"), 400

        print(f"Checkout Session ID: {session.id}")  # Log session ID
        return jsonify({'id': session.id})
    except Exception as e:
        print(f"Error: {str(e)}")  # Log any errors
        return jsonify(error=str(e)), 403

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return Response(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return Response(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_details', {}).get('email')
        print(f"Checkout Session Completed with email: {customer_email}")
        # Here you can add your logic to save the email or perform other actions

    return Response(status=200)

if __name__ == '__main__':
    app.run(port=4242)
