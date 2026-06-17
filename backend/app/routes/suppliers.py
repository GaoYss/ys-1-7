from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Supplier

suppliers_bp = Blueprint("suppliers", __name__)


@suppliers_bp.get("")
def list_suppliers():
    suppliers = Supplier.query.order_by(Supplier.created_at.desc()).all()
    return jsonify([supplier.to_dict() for supplier in suppliers])


@suppliers_bp.post("")
def create_supplier():
    data = request.get_json() or {}
    if not data.get("name") or not data.get("contact") or not data.get("phone"):
        return {"error": "供应商名称、联系人、电话不能为空"}, 400
    if Supplier.query.filter_by(name=data["name"]).first():
        return {"error": "该供应商名称已存在"}, 400
    supplier = Supplier(
        name=data["name"],
        contact=data["contact"],
        phone=data["phone"],
        address=data.get("address"),
        rating=int(data.get("rating", 5)),
        status=data.get("status", "active"),
    )
    db.session.add(supplier)
    db.session.commit()
    return supplier.to_dict(), 201


@suppliers_bp.put("/<int:supplier_id>")
def update_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json() or {}

    new_name = data.get("name", supplier.name)
    if new_name != supplier.name and Supplier.query.filter_by(name=new_name).first():
        return {"error": "该供应商名称已存在"}, 400

    supplier.name = new_name
    supplier.contact = data.get("contact", supplier.contact)
    supplier.phone = data.get("phone", supplier.phone)
    supplier.address = data.get("address", supplier.address)
    supplier.rating = int(data.get("rating", supplier.rating))
    supplier.status = data.get("status", supplier.status)

    db.session.commit()
    return supplier.to_dict()


@suppliers_bp.delete("/<int:supplier_id>")
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    if supplier.quotes:
        return {"error": "该供应商存在报价记录，无法删除"}, 400
    if supplier.orders:
        return {"error": "该供应商存在采购订单，无法删除"}, 400
    db.session.delete(supplier)
    db.session.commit()
    return "", 204
