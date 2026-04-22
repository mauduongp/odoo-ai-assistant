from odoo import _, models
from odoo.exceptions import UserError


class AiToolService(models.AbstractModel):
    _name = "m_ai.tool.service"
    _description = "AI Tool Service"

    _ALLOWED_TOOLS = {
        "query_records",
        "read_records",
        "prepare_create_record",
        "create_record",
    }
    _MAX_LIMIT = 20

    def execute_tool(self, tool_name, arguments):
        if tool_name not in self._ALLOWED_TOOLS:
            raise UserError(_("Tool '%s' is not allowed.") % (tool_name or ""))

        arguments = arguments or {}
        if tool_name == "query_records":
            return self._tool_query_records(arguments)
        if tool_name == "read_records":
            return self._tool_read_records(arguments)
        if tool_name == "prepare_create_record":
            return self._tool_prepare_create_record(arguments)
        if tool_name == "create_record":
            return self._tool_create_record(arguments)
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
        ids = self._normalize_ids(arguments.get("ids"))

        model = self._validate_model_and_fields(model_name, fields)
        if not ids:
            raise UserError(_("Argument 'ids' must be a list of integers."))
        if len(ids) > self._MAX_LIMIT:
            ids = ids[: self._MAX_LIMIT]

        recordset = self.env[model].browse(ids).exists()
        return {
            "model": model_name,
            "count": len(recordset),
            "records": self._serialize_records(recordset, fields),
        }

    def _tool_prepare_create_record(self, arguments):
        model_name = (arguments.get("model") or "").strip()
        values = arguments.get("values") or {}

        model = self._validate_create_model(model_name)
        if not isinstance(values, dict) or not values:
            raise UserError(_("Argument 'values' must be a non-empty object."))
        sanitized_values, dropped_fields = self._sanitize_create_values(model, values)
        if not sanitized_values:
            raise UserError(
                _(
                    "No allowed fields remain after sanitization for model '%s'."
                )
                % model_name
            )
        normalized_values = self._normalize_create_values(model, sanitized_values)
        warnings = []
        if dropped_fields:
            warnings.append(
                _(
                    "Dropped non-allowed create fields for model '%(model)s': %(fields)s"
                )
                % {"model": model_name, "fields": ", ".join(dropped_fields)}
            )
        return {
            "model": model_name,
            "prepared": True,
            "values": normalized_values,
            "warnings": warnings,
        }

    def _tool_create_record(self, arguments):
        model_name = (arguments.get("model") or "").strip()
        values = arguments.get("values") or {}

        model = self._validate_create_model_and_values(model_name, values)
        normalized_values = self._normalize_create_values(model, values)
        record = self.env[model].create(normalized_values)
        return {
            "model": model_name,
            "count": 1,
            "record_id": record.id,
            "record_name": record.display_name,
            "values": normalized_values,
        }

    def _validate_model_and_fields(self, model_name, fields):
        allowed_models = self._get_allowed_models()
        if model_name not in allowed_models:
            raise UserError(_("Model '%s' is not allowed for AI tools.") % model_name)
        if not isinstance(fields, list) or not fields:
            raise UserError(_("Argument 'fields' must be a non-empty list."))

        allowed_fields = allowed_models[model_name]
        forbidden = [field for field in fields if field not in allowed_fields]
        if forbidden:
            raise UserError(
                _("Fields are not allowed for model '%s': %s")
                % (model_name, ", ".join(forbidden))
            )
        return model_name

    def _validate_create_model_and_values(self, model_name, values):
        model_name = self._validate_create_model(model_name)
        if not isinstance(values, dict) or not values:
            raise UserError(_("Argument 'values' must be a non-empty object."))

        allowed_fields = self._get_create_allowed_models()[model_name]
        forbidden = [field for field in values.keys() if field not in allowed_fields]
        if forbidden:
            raise UserError(
                _("Fields are not allowed for create on model '%s': %s")
                % (model_name, ", ".join(forbidden))
            )
        return model_name

    def _validate_create_model(self, model_name):
        allowed_models = self._get_create_allowed_models()
        if model_name not in allowed_models:
            raise UserError(
                _("Model '%s' is not allowed for AI create tools.") % model_name
            )
        return model_name

    def _sanitize_create_values(self, model_name, values):
        allowed_fields = self._get_create_allowed_models()[model_name]
        sanitized = {}
        dropped = []
        for field_name, field_value in values.items():
            if field_name in allowed_fields:
                sanitized[field_name] = field_value
            else:
                dropped.append(field_name)
        return sanitized, dropped

    def _normalize_ids(self, raw_ids):
        if raw_ids is None:
            return []
        if isinstance(raw_ids, int):
            return [raw_ids]
        if isinstance(raw_ids, str):
            parts = [item.strip() for item in raw_ids.split(",") if item.strip()]
            normalized = []
            for item in parts:
                if item.isdigit():
                    normalized.append(int(item))
            return normalized
        if isinstance(raw_ids, list):
            normalized = []
            for item in raw_ids:
                if isinstance(item, int):
                    normalized.append(item)
                elif isinstance(item, str) and item.strip().isdigit():
                    normalized.append(int(item.strip()))
            return normalized
        return []

    def _get_allowed_models(self):
        """Return mapping: model -> set(allowed fields). Overridden by tool modules."""
        return {}

    def _get_create_allowed_models(self):
        """Return mapping: model -> set(allowed create fields)."""
        return {}

    def _normalize_create_values(self, model_name, values):
        model = self.env[model_name]
        normalized = {}
        for field_name, value in values.items():
            field = model._fields.get(field_name)
            if field and field.type == "many2one":
                normalized[field_name] = self._normalize_many2one_create_value(value)
            else:
                normalized[field_name] = value
        return normalized

    def _normalize_many2one_create_value(self, value):
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            text = value.strip()
            if text.isdigit():
                return int(text)
            raise UserError(
                _(
                    "Many2one values must be an integer id or object with an 'id' key."
                )
            )
        if isinstance(value, dict):
            candidate = value.get("id")
            if isinstance(candidate, int):
                return candidate
            if isinstance(candidate, str) and candidate.strip().isdigit():
                return int(candidate.strip())
        raise UserError(
            _("Many2one values must be an integer id or object with an 'id' key.")
        )

    def _serialize_records(self, records, fields):
        rows = []
        read_fields = list(fields)
        if "id" not in read_fields:
            read_fields.append("id")
        for record in records:
            values = record.read(read_fields)[0]
            serialized = {}
            for field_name in fields:
                serialized[field_name] = self._serialize_field(record, field_name, values[field_name])
            serialized["id"] = record.id
            rows.append(serialized)
        return rows

    def _serialize_field(self, record, field_name, value):
        try:
            field = record._fields[field_name]
            if field.type == "many2one":
                if isinstance(value, (tuple, list)):
                    pair = list(value[:2])
                    if len(pair) == 2:
                        return {"id": pair[0], "name": pair[1]}
                    if len(pair) == 1:
                        related = record[field_name]
                        return {
                            "id": pair[0],
                            "name": related.display_name if related else str(pair[0]),
                        }
                related = record[field_name]
                if related:
                    return {"id": related.id, "name": related.display_name}
                return False
            if field.type == "selection":
                selection = dict(record.fields_get([field_name])[field_name]["selection"])
                return {"value": value, "label": selection.get(value, value)}
            return value
        except Exception:
            # Keep tool responses robust even when ORM value shapes vary.
            return value
