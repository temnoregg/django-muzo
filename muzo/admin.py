from django.contrib import admin

from models import Request, Response


class RequestAdmin(admin.ModelAdmin):
    list_display = ('ORDERNUMBER', 'MERORDERNUM', 'AMOUNT', 'CURRENCY', 'DATE')


class ResponseAdmin(admin.ModelAdmin):
    list_display = ('ORDERNUMBER', 'MERORDERNUM', 'PRCODE', 'SRCODE', 'RESULTTEXT', 'DATE')


admin.site.register(Request, RequestAdmin)
admin.site.register(Response, ResponseAdmin)