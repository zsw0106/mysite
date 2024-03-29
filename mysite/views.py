import datetime
from django.shortcuts import render, redirect
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models import Sum
from django.core.cache import cache
from django.urls import reverse
from read_statistics.utils import get_seven_days_read_data, get_today_hot_data, get_yesterday_hot_data
from bbs.models import BBS


def get_7_days_hot_bbss():
    today = timezone.now().date()
    date = today - datetime.timedelta(days=7)
    bbss = BBS.objects \
                .filter(read_details__date__lt=today, read_details__date__gte=date) \
                .values('id', 'title') \
                .annotate(read_num_sum=Sum('read_details__read_num')) \
                .order_by('-read_num_sum')
    return bbss[:7]

def home(request):
    bbs_content_type = ContentType.objects.get_for_model(BBS)
    dates, read_nums = get_seven_days_read_data(bbs_content_type)

    # 获取7天热门博客的缓存数据
    hot_bbss_for_7_days = cache.get('hot_bbss_for_7_days')
    if hot_bbss_for_7_days is None:
        hot_bbss_for_7_days = get_7_days_hot_bbss()
        cache.set('hot_bbss_for_7_days', hot_bbss_for_7_days, 3600)

    context = {}
    context['dates'] = dates
    context['read_nums'] = read_nums
    context['today_hot_data'] = get_today_hot_data(bbs_content_type)
    context['yesterday_hot_data'] = get_yesterday_hot_data(bbs_content_type)
    context['hot_bbss_for_7_days'] = hot_bbss_for_7_days
    return render(request, 'home.html', context)
