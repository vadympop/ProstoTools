from django.db import models
from django.forms.models import model_to_dict


class TemplateRenderingModel:
    def __init__(self, model: models.base.ModelBase, **kwargs):
        self.raw = {**model_to_dict(model), **kwargs}
        for key, value in self.raw.items():
            self.__setattr__(key, value)

    def __repr__(self):
        return f"TemplateRenderingModel({self.raw})"