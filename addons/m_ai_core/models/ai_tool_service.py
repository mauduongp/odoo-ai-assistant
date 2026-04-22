from odoo import _, models
from odoo.exceptions import UserError


class AiToolService(models.AbstractModel):
    _name = "m_ai.tool.service"
    _description = "AI Tool Service"

    _ALLOWED_MODELS = {
        "sale.order": {
            "name",
            "client_order_ref",
            "state",
            "invoice_status",
            "amount_total",
            "currency_id",
            "partner_id",
            "date_order",
            "commitment_date",
            "create_date",
            "write_date",
        }
    }

    _ALLOWED_TOOLS = {"query_records", "read_records"}
    _MAX_LIMIT = 20

    def execute_tool(self, tool_name, arguments):
        if tool_name not in self._ALLOWED_TOOLS:
            raise UserError(_("Tool '%s' is not allowed.") % (tool_name or ""))

        arguments = arguments or {}
        if tool_name == "query_records":
            return self._tool_query_records(arguments)
        if tool_name == "read_records":
            return self._tool_read_records(arguments)
        raise UserError(_("Tool '%s' is not implemented.") % tool_name)

    def _tool_query_records(self, arguments):
        model_name = (arguments.get("model") or "").strip()
        fields = arguments.get("fields") or []
        domain = arguments.get("domain") or []
        limit = int(arguments.get("limit") or 5)

        model = self._validate_model_and_fields(model_name, fields)
        if not isinstance(domain, list):
            raise UserError(_("Argument 'domain' must be a list."))
        if limit < 1:
            limit = 1
        limit = min(limit, self._MAX_LIMIT)

        recordset = self.env[model].search(domain, limit=limit)
        return {
            "model": model_name,
            "count": len(recordset),
            "records": self._serialize_records(recordset, fields),
        }

    def _tool_read_records(self, arguments):
        model_name = (arguments.get("model") or "").strip()
        fields = arguments.get("fields") or []
        ids = arguments.get("ids") or []

        model = self._validate_model_and_fields(model_name, fields)
        if not isinstance(ids, list) or not all(isinstance(item, int) for item in ids):
            raise UserError(_("Argument 'ids' must be a list of integers."))
        if len(ids) > self._MAX_LIMIT:
            ids = ids[: self._MAX_LIMIT]

        recordset = self.env[model].browse(ids).exists()
        return {
            "model": model_name,
            "count": len(recordset),
            "records": self._serialize_records(recordset, fields),
        }

    def _validate_model_and_fields(self, model_name, fields):
        if model_name not in self._ALLOWED_MODELS:
            raise UserError(_("Model '%s' is not allowed for AI tools.") % model_name)
        if not isinstance(fields, list) or not fields:
            raise UserError(_("Argument 'fields' must be a non-empty list."))

        allowed_fields = self._ALLOWED_MODELS[model_name]
        forbidden = [field for field in fields if field not in allowed_fields]
        if forbidden:
            raise UserError(
                _("Fields are not allowed for model '%s': %s")
                % (model_name, ", ".join(forbidden))
            )
        return model_name

    def _serialize_records(self, records, fields):
        rows = []
        for record in records:
            values = record.read(fields)[0]
            serialized = {}
            for field_name in fields:
                serialized[field_name] = self._serialize_field(record, field_name, values[field_name])
            rows.append(serialized)
        return rows

    def _serialize_field(self, record, field_name, value):
        field = record._fields[field_name]
        if field.type == "many2one":
            if isinstance(value, (tuple, list)):
                if len(value) >= 2:
                    return {"id": value[0], "name": value[1]}
                if len(value) == 1:
                    related = record[field_name]
                    return {
                        "id": value[0],
                        "name": related.display_name if related else str(value[0]),
                    }
            return False
        if field.type == "selection":
            selection = dict(record.fields_get([field_name])[field_name]["selection"])
            return {"value": value, "label": selection.get(value, value)}
        return value
