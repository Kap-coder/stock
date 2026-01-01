from rest_framework import serializers
from .models import Sale, SaleItem, Payment, Invoice
from inventory.models import Product

class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(required=False, allow_null=True, allow_blank=True) # Allow write for custom items
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'subtotal']
        read_only_fields = ['subtotal'] # product_name is now writable

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)
    payments = PaymentSerializer(many=True, read_only=True)
    invoice = InvoiceSerializer(read_only=True)
    cashier_name = serializers.ReadOnlyField(source='cashier.username')

    class Meta:
        model = Sale
        fields = ['id', 'shop', 'cashier', 'cashier_name', 'created_at', 'total_amount', 'payment_method', 'items', 'payments', 'invoice']
        read_only_fields = ['total_amount', 'cashier', 'shop']

    def validate(self, data):
        items_data = data.get('items')
        if not items_data:
             raise serializers.ValidationError("Aucun article dans la vente.")
             
        for item in items_data:
            product = item.get('product')
            quantity = item.get('quantity')
            
            # Stock Validation for existing products
            if product:
                if product.quantity < quantity:
                    raise serializers.ValidationError(
                        f"Stock insuffisant pour '{product.name}'. Disponible: {product.quantity}"
                    )
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(**validated_data)
        total = 0
        
        for item_data in items_data:
            product = item_data.get('product')
            quantity = item_data['quantity']
            # Use provided price (for custom items) or product price (if product exists)
            price = item_data.get('price')
            if price is None and product:
                 price = product.selling_price
            
            if price is None:
                price = 0

            subtotal = price * quantity
            
            # Use provided name for custom items, or product name
            custom_name = item_data.get('product_name')
            product_name = product.name if product else (custom_name or "Vente Libre")
            
            item = SaleItem.objects.create(
                sale=sale, 
                product=product, # Can be None
                product_name=product_name,
                quantity=quantity, 
                price=price, 
                subtotal=subtotal
            )
            total += subtotal
            
            if product:
                # Create StockMovement
                from inventory.models import StockMovement
                StockMovement.objects.create(
                    product=product,
                    quantity=quantity,
                    movement_type=StockMovement.MovementType.OUT,
                    reason=f"Vente #{sale.id}"
                )
                
                # Decrement stock
                product.quantity -= quantity
                product.save()

        sale.total_amount = total
        sale.save()
        return sale
