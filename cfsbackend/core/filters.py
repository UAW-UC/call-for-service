from django.forms import ModelChoiceField
from django_filters import FilterSet, DateFromToRangeFilter, MethodFilter, \
    RangeFilter, ModelChoiceFilter
from django_filters.fields import RangeField
from django.db.models import Q
from django import forms

from .models import Call, CallUnit, Squad, ZipCode, CallSource


class DurationRangeField(RangeField):
    def __init__(self, *args, **kwargs):
        fields = (
            forms.DurationField(),
            forms.DurationField())
        super().__init__(fields, *args, **kwargs)


class ChoiceMethodFilter(MethodFilter):
    field_class = forms.ChoiceField


class DurationRangeFilter(RangeFilter):
    field_class = DurationRangeField

    def filter(self, qs, value):
        if value:
            if value.start is not None and value.stop is not None:
                lookup = '%s__range' % self.name
                return self.get_method(qs)(
                    **{lookup: (value.start, value.stop)})
            else:

                if value.start is not None:
                    qs = self.get_method(qs)(
                        **{'%s__gte' % self.name: value.start})
                if value.stop is not None:
                    qs = self.get_method(qs)(
                        **{'%s__lte' % self.name: value.stop})
        return qs


class CallFilter(FilterSet):
    time_received = DateFromToRangeFilter()
    time_routed = DateFromToRangeFilter()
    time_finished = DateFromToRangeFilter()
    time_closed = DateFromToRangeFilter()
    officer_response_time = DurationRangeFilter()
    overall_response_time = DurationRangeFilter()
    unit = ChoiceMethodFilter(action='filter_unit',
                              choices=CallUnit.objects.all().values_list('call_unit_id', 'descr'))
    squad = ChoiceMethodFilter(action='filter_squad',
                              choices=Squad.objects.all().values_list('squad_id', 'descr'))

    # These need to be explicitly instantiated because we need to set the label on them.
    # Their labels all default to "Squad" otherwise.
    first_dispatched__squad = ModelChoiceFilter(label='First dispatched squad',
                                              queryset=Squad.objects.all())
    primary_unit__squad = ModelChoiceFilter(label='Primary unit squad',
                                              queryset=Squad.objects.all())
    reporting_unit__squad = ModelChoiceFilter(label='Reporting unit squad',
                                              queryset=Squad.objects.all())
    initiated_by = ChoiceMethodFilter(label="Initiated by",
                                      action="filter_initiated_by",
                                      choices=[('Self', 'Self'), ('Citizen', 'Citizen')])

    class Meta:
        model = Call
        fields = ['zip_code', 'district', 'sector', 'beat',
                  'call_source', 'nature', 'priority', 'close_code',
                  'primary_unit', 'first_dispatched', 'reporting_unit',
                  'cancelled'
                  ]

    def filter_unit(self, queryset, value):
        if value:
            query = Q(primary_unit_id=value) | Q(first_dispatched_id=value) | Q(
                reporting_unit_id=value)
            return queryset.filter(query)
        else:
            return queryset

    def filter_squad(self, queryset, value):
        if value:
            query = Q(primary_unit__squad_id=value) | Q(first_dispatched__squad_id=value) | Q(
                reporting_unit__squad_id=value)
            return queryset.filter(query)
        else:
            return queryset

    def filter_initiated_by(self, queryset, value):
        if value == "Self":
            return queryset.filter(call_source=CallSource.objects.get(descr="Self Initiated"))
        elif value == "Citizen":
            return queryset.exclude(call_source=CallSource.objects.get(descr="Self Initiated"))
        else:
            return queryset

class SummaryFilter(FilterSet):
    class Meta:
        model = Call
        fields = ['month_received', 'dow_received', 'hour_received']