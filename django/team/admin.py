from django.apps import apps
from django.contrib import admin

models = apps.get_models()

for model in models:
    if "team.models" in str(model):
        admin.site.register(model)
