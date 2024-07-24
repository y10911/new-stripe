from flask import Flask, jsonify, request
import stripe

app = Flask(__name__)

# Use a test secret key from Stripe for demo purposes
stripe.api_key = 'sk_test_51Of6goKZ0oo6AUWAhVAGBbJgiaBVpVUkPLBQOdVE4RKnE38lsscMVc85p2j0s6EjAD0bBOxz4pUIAh13t3UwWiTe00kHiko9gx'

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
                success_url=data['success_url'],
                cancel_url=data['cancel_url'],
                allow_promotion_codes=True  # Add this line to allow promotion codes
            )
        elif purchase_type == "membership":
            # Create a Stripe product for the membership
            product = stripe.Product.create(name=service_name + " Membership")

            # Create a Stripe price for the membership
            price = stripe.Price.create(
                unit_amount=50000,  # $500 in cents
                currency="usd",
                recurring={"interval": "month"},
                product=product.id,
            )

            # Create a Stripe Checkout session for membership
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price.id,
                        'quantity': 1,
                    }
                ],
                mode='subscription',
                success_url=data['success_url'],
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

if __name__ == '__main__':
    app.run(port=4242)
