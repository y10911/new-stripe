from flask import Flask, jsonify, request
import stripe

app = Flask(__name__)

# Use a test secret key from Stripe for demo purposes
stripe.api_key = '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'

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', 'https://www.designteam.co/')
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
    base_price = data.get('basePrice')  # Get base price
    additional_fee = data.get('additionalFee', 0)  # Additional fee if any

    print(f"Received values: service_name={service_name}, quantity={quantity}, subtotal={subtotal}, purchase_type={purchase_type}, min_order={min_order}, unit_type={unit_type}, base_price={base_price}, additional_fee={additional_fee}")

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
                success_url="https://www.designteam.co/payment-success",
                cancel_url=data['cancel_url'],
                allow_promotion_codes=True,  # Add this line to allow promotion codes
                client_reference_id=service_name  # Pass the service name as client reference
            )
        elif purchase_type == "membership":
            # Create a Stripe product for the membership with a description
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

            # Add the free order as a line item if the total is less than or equal to base_price * min_order
            if subtotal <= (base_price * min_order * 100):  # Ensure subtotal is in cents
                print(f"Adding free line item for {quantity} {unit_type}")
                line_items.append(
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"{service_name} (Free)",
                                'description': f"{quantity} {unit_type}",
                            },
                            'unit_amount': 0,
                        },
                        'quantity': quantity,
                    }
                )

            # If there's an additional fee, add it as a one-time charge
            if additional_fee > 0:
                additional_units = quantity - min_order
                line_items.append(
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"{service_name} Additional Fee",
                                'description': f"{additional_units} additional {unit_type}",
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
                success_url="https://www.designteam.co/membership-success",
                cancel_url=data['cancel_url'],
                allow_promotion_codes=True,  # Add this line to allow promotion codes
                client_reference_id=service_name  # Pass the service name as client reference
            )
        else:
            return jsonify(error="Invalid purchase type"), 400

        print(f"Checkout Session ID: {session.id}")  # Log session ID
        return jsonify({'id': session.id})
    except Exception as e:
        print(f"Error: {str(e)}")  # Log any errors
        return jsonify(error=str(e)), 403

if __name__ == '__main__':
    app.run(port=4242, debug=True)
