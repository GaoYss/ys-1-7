from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Ingredient, Supplier, SupplierQuote

quotes_bp = Blueprint("quotes", __name__)


@quotes_bp.get("")
def list_quotes():
    ingredient_id = request.args.get("ingredientId")
    supplier_id = request.args.get("supplierId")

    query = SupplierQuote.query
    if ingredient_id:
        query = query.filter(SupplierQuote.ingredient_id == ingredient_id)
    if supplier_id:
        query = query.filter(SupplierQuote.supplier_id == supplier_id)

    quotes = query.order_by(SupplierQuote.ingredient_id, SupplierQuote.unit_price).all()
    return jsonify([q.to_dict() for q in quotes])


@quotes_bp.post("")
def create_quote():
    data = request.get_json() or {}
    if not data.get("ingredientId") or not data.get("supplierId") or not data.get("unitPrice"):
        return {"error": "原料、供应商、单价不能为空"}, 400
    existing = SupplierQuote.query.filter_by(
        ingredient_id=data["ingredientId"],
        supplier_id=data["supplierId"],
        status="active",
    ).first()
    if existing:
        return {"error": "该供应商已存在此原料的有效报价，可先停用旧报价"}, 400
    quote = SupplierQuote(
        ingredient_id=data["ingredientId"],
        supplier_id=data["supplierId"],
        unit_price=float(data["unitPrice"]),
        delivery_days=int(data.get("deliveryDays", 3)),
        status=data.get("status", "active"),
    )
    db.session.add(quote)
    db.session.commit()
    return quote.to_dict(), 201


@quotes_bp.put("/<int:quote_id>")
def update_quote(quote_id):
    quote = SupplierQuote.query.get_or_404(quote_id)
    data = request.get_json() or {}

    new_ingredient_id = data.get("ingredientId", quote.ingredient_id)
    new_supplier_id = data.get("supplierId", quote.supplier_id)
    new_status = data.get("status", quote.status)

    if new_status == "active" and (
        new_ingredient_id != quote.ingredient_id or new_supplier_id != quote.supplier_id
    ):
        existing = SupplierQuote.query.filter(
            SupplierQuote.ingredient_id == new_ingredient_id,
            SupplierQuote.supplier_id == new_supplier_id,
            SupplierQuote.status == "active",
            SupplierQuote.id != quote_id,
        ).first()
        if existing:
            return {"error": "该供应商已存在此原料的其他有效报价"}, 400

    quote.ingredient_id = new_ingredient_id
    quote.supplier_id = new_supplier_id
    quote.unit_price = float(data.get("unitPrice", quote.unit_price))
    quote.delivery_days = int(data.get("deliveryDays", quote.delivery_days))
    quote.status = new_status

    db.session.commit()
    return quote.to_dict()


@quotes_bp.delete("/<int:quote_id>")
def delete_quote(quote_id):
    quote = SupplierQuote.query.get_or_404(quote_id)
    db.session.delete(quote)
    db.session.commit()
    return "", 204


@quotes_bp.get("/recommend")
def recommend_quotes():
    ingredient_id = request.args.get("ingredientId")
    all_query = SupplierQuote.query
    if ingredient_id:
        all_query = all_query.filter(SupplierQuote.ingredient_id == ingredient_id)
    all_quotes = all_query.all()

    grouped = {}
    for q in all_quotes:
        iid = q.ingredient_id
        grouped.setdefault(iid, []).append(q)

    results = []
    for iid, all_group in grouped.items():
        active_group = [
            q for q in all_group
            if q.status == "active" and q.supplier and q.supplier.status == "active"
        ]
        inactive_group = [q for q in all_group if q not in active_group]

        scored = []
        if active_group:
            prices = [q.unit_price for q in active_group]
            min_price = min(prices) if prices else 1
            max_delivery = max(q.delivery_days for q in active_group) or 1
            min_delivery = min(q.delivery_days for q in active_group)

            for q in active_group:
                price_score = round(min_price / q.unit_price if q.unit_price else 0, 4)
                rating_score = round((q.supplier.rating if q.supplier else 0) / 5, 4)
                delivery_score = round(1 - (q.delivery_days / (max_delivery + 1)), 4)
                total = round(price_score * 0.5 + rating_score * 0.3 + delivery_score * 0.2, 4)

                reasons = []
                if q.unit_price == min_price:
                    reasons.append("价格最低")
                else:
                    diff_pct = round((q.unit_price - min_price) / min_price * 100, 1)
                    reasons.append(f"高于最低价 {diff_pct}%")
                if q.supplier and q.supplier.rating == 5:
                    reasons.append("评级最高★★★★★")
                elif q.supplier and q.supplier.rating >= 4:
                    reasons.append(f"评级良好{'★' * q.supplier.rating}")
                elif q.supplier:
                    reasons.append(f"评级{'★' * q.supplier.rating}")
                if q.delivery_days == min_delivery:
                    reasons.append("交付最快")
                elif q.delivery_days >= max_delivery:
                    reasons.append("交付周期较长")

                scored.append({
                    **q.to_dict(),
                    "score": total,
                    "scoreBreakdown": {
                        "price": price_score,
                        "rating": rating_score,
                        "delivery": delivery_score,
                    },
                    "reasons": reasons,
                    "excluded": False,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)

        for q in inactive_group:
            exclude_reason = []
            if q.status != "active":
                exclude_reason.append("报价已停用")
            if q.supplier and q.supplier.status != "active":
                exclude_reason.append("供应商已停用")
            if not q.supplier:
                exclude_reason.append("供应商不存在")
            scored.append({
                **q.to_dict(),
                "score": None,
                "scoreBreakdown": {"price": None, "rating": None, "delivery": None},
                "reasons": exclude_reason,
                "excluded": True,
                "excludeReason": "、".join(exclude_reason) if exclude_reason else "不参与推荐",
            })

        ingredient = Ingredient.query.get(iid)
        best = scored[0] if scored and not scored[0]["excluded"] else None
        second = None
        for s in scored[1:]:
            if not s["excluded"]:
                second = s
                break

        summary_reasons = []
        if best and second:
            price_save = round((second["unitPrice"] - best["unitPrice"]) / second["unitPrice"] * 100, 1)
            if price_save > 0:
                summary_reasons.append(f"比次选节省 {price_save}% 成本")
            if best["deliveryDays"] < second["deliveryDays"]:
                summary_reasons.append(f"比次选快 {second['deliveryDays'] - best['deliveryDays']} 天交付")
            if best["supplierRating"] and second["supplierRating"] and best["supplierRating"] > second["supplierRating"]:
                summary_reasons.append(f"评级比次选高 {best['supplierRating'] - second['supplierRating']} 星")

        active_count = len([s for s in scored if not s["excluded"]])
        results.append({
            "ingredientId": iid,
            "ingredientName": ingredient.name if ingredient else None,
            "ingredientUnit": ingredient.unit if ingredient else None,
            "quotes": scored,
            "recommended": best,
            "summaryReasons": summary_reasons,
            "quoteCount": active_count,
            "totalQuoteCount": len(scored),
        })

    results.sort(key=lambda x: x["ingredientId"])
    return jsonify(results)


@quotes_bp.get("/options")
def quote_options():
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    suppliers = Supplier.query.filter_by(status="active").order_by(Supplier.name).all()
    return {
        "ingredients": [item.to_dict() for item in ingredients],
        "suppliers": [s.to_dict() for s in suppliers],
    }
