from tortoise import fields
from tortoise.models import Model


class AiContentTask(Model):
    id = fields.IntField(pk=True)
    operator_id = fields.IntField()
    status = fields.CharField(max_length=20, default="pending")
    content_types = fields.CharField(max_length=255)
    book_ids = fields.CharField(max_length=500)
    tone = fields.CharField(max_length=32, default="healing")
    length = fields.CharField(max_length=16, default="medium")
    extra_prompt = fields.TextField(null=True)
    write_mode = fields.CharField(max_length=20, default="empty_only")
    provider_mode = fields.CharField(max_length=16, default="mock")
    model_name = fields.CharField(max_length=100, null=True)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    finished_at = fields.DatetimeField(null=True)

    class Meta:
        table = "ai_content_task"


class AiContentItem(Model):
    id = fields.IntField(pk=True)
    task_id = fields.IntField()
    book_id = fields.IntField()
    content_type = fields.CharField(max_length=40)
    target_field = fields.CharField(max_length=64)
    source_text = fields.TextField(null=True)
    generated_text = fields.TextField(null=True)
    edited_text = fields.TextField(null=True)
    status = fields.CharField(max_length=20, default="draft")
    error_message = fields.TextField(null=True)
    applied_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "ai_content_item"
