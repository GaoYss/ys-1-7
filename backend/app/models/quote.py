from datetime import datetime

from ..extensions import db


class SupplierQuote(db.Model):
    __tablename__ = "supplier_quotes"

    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    delivery_days = db.Column(db.Integer, nullable=False, default=3)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ingredient = db.relationship("Ingredient", backref="quotes")
    supplier = db.relationship("Supplier", backref="quotes")

    def to_dict(self):
        return {
            "id": self.id,
            "ingredientId": self.ingredient_id,
            "ingredientName": self.ingredient.name if self.ingredient else None,
            "supplierId": self.supplier_id,
            "supplierName": self.supplier.name if self.supplier else None,
            "supplierRating": self.supplier.rating if self.supplier else None,
            "supplierStatus": self.supplier.status if self.supplier else None,
            "unitPrice": self.unit_price,
            "deliveryDays": self.delivery_days,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
