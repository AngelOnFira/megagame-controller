from django.contrib import admin
from django.apps import apps

models = apps.get_models()

for model in models:
    if "id_emojis.models" in str(model):
        admin.site.register(model)
