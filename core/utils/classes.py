import typing

from core.utils.other import model_to_dict as cache_item_to_dict
from core.services.cache.cache_manager import CacheItem
from django.db import models
from django.forms.models import model_to_dict


class TemplateRenderingModel:
    def __init__(self, model: typing.Union[models.base.ModelBase, CacheItem], **kwargs):
        self.raw = kwargs
        if isinstance(model, models.base.ModelBase):
            self.raw.update(**model_to_dict(model))
        else:
            self.raw.update(**cache_item_to_dict(model))

        for key, value in self.raw.items():
            self.__setattr__(key, value)

    def __repr__(self):
        return f"TemplateRenderingModel({self.raw})"