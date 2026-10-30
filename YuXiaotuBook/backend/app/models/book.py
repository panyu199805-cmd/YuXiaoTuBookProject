from tortoise import fields
from tortoise.models import Model


class Book(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    author = fields.CharField(max_length=100)
    cover = fields.CharField(max_length=500)
    category_id = fields.IntField()
    price = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = fields.IntField(default=0)
    summary = fields.TextField(null=True)
    highlight = fields.CharField(max_length=500, null=True)
    target_audience = fields.CharField(max_length=200, null=True)
    status = fields.CharField(max_length=20, default="draft")
    view_count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "book"


class BookVideo(Model):
    id = fields.IntField(pk=True)
    book_id = fields.IntField()
    sort_order = fields.IntField(default=0)
    video_cover = fields.CharField(max_length=500)
    video_url = fields.CharField(max_length=500)
    video_duration = fields.FloatField(default=0)
    video_intro = fields.TextField(null=True)
    explain_content = fields.TextField(null=True)
    play_count = fields.IntField(default=0)
    status = fields.IntField(default=1)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "book_video"
