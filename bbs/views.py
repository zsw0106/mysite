from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Count
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse

from .models import BBS, BBSType
from read_statistics.utils import read_statistics_once_read
from .forms import BBSForm


def get_bbs_list_common_data(request, bbss_all_list):
    paginator = Paginator(bbss_all_list, settings.EACH_PAGE_BBSS_NUMBER)
    page_num = request.GET.get('page', 1) # 获取url的页面参数（GET请求）
    page_of_bbss = paginator.get_page(page_num)
    currentr_page_num = page_of_bbss.number # 获取当前页码
    # 获取当前页码前后各2页的页码范围
    page_range = list(range(max(currentr_page_num - 2, 1), currentr_page_num)) + \
                 list(range(currentr_page_num, min(currentr_page_num + 2, paginator.num_pages) + 1))
    # 加上省略页码标记
    if page_range[0] - 1 >= 2:
        page_range.insert(0, '...')
    if paginator.num_pages - page_range[-1] >= 2:
        page_range.append('...')
    # 加上首页和尾页
    if page_range[0] != 1:
        page_range.insert(0, 1)
    if page_range[-1] != paginator.num_pages:
        page_range.append(paginator.num_pages)

    # 获取日期归档对应的博客数量
    bbs_dates = BBS.objects.dates('created_time', 'month', order="DESC")
    bbs_dates_dict = {}
    for bbs_date in bbs_dates:
        bbs_count = BBS.objects.filter(created_time__year=bbs_date.year, 
                                         created_time__month=bbs_date.month).count()
        bbs_dates_dict[bbs_date] = bbs_count

    context = {}
    context['bbss'] = page_of_bbss.object_list
    context['page_of_bbss'] = page_of_bbss
    context['page_range'] = page_range
    context['bbs_types'] = BBSType.objects.annotate(bbs_count=Count('bbs'))
    context['bbs_dates'] = bbs_dates_dict
    return context

def bbs_list(request):
    bbss_all_list = BBS.objects.all()
    context = get_bbs_list_common_data(request, bbss_all_list)
    return render(request, 'bbs/bbs_list.html', context)

def bbss_with_type(request, bbs_type_pk):
    bbs_type = get_object_or_404(BBSType, pk=bbs_type_pk)
    bbss_all_list = BBS.objects.filter(bbs_type=bbs_type)
    context = get_bbs_list_common_data(request, bbss_all_list)
    context['bbs_type'] = bbs_type
    return render(request, 'bbs/bbss_with_type.html', context)

def bbss_with_date(request, year, month):
    bbss_all_list = BBS.objects.filter(created_time__year=year, created_time__month=month)
    context = get_bbs_list_common_data(request, bbss_all_list)
    context['bbss_with_date'] = '%s年%s月' % (year, month)
    return render(request, 'bbs/bbss_with_date.html', context)

def bbs_detail(request, bbs_pk):
    bbs = get_object_or_404(BBS, pk=bbs_pk)
    read_cookie_key = read_statistics_once_read(request, bbs)

    context = {}
    context['previous_bbs'] = BBS.objects.filter(created_time__gt=bbs.created_time).last()
    context['next_bbs'] = BBS.objects.filter(created_time__lt=bbs.created_time).first()
    context['bbs'] = bbs
    response = render(request, 'bbs/bbs_detail.html', context) # 响应
    response.set_cookie(read_cookie_key, 'true') # 阅读cookie标记
    return response

# 添加帖子
def add_bbs(request):
    if request.method == 'POST':
        bbs_form = BBSForm(request.POST)
        if bbs_form.is_valid():
            bbs_form.instance.author = request.user #获取登录用户实例，创建帖子
            bbs_form.save()
            return redirect(request.GET.get('from', reverse('home')))
    else:
        bbs_form = BBSForm()
    return render(request, 'bbs/add_bbs.html', {'bbs_form':bbs_form})

# 删文章
def bbs_delete(request, id):
    # 根据 id 获取需要删除的文章
    bbs = BBS.objects.get(id=id)
    # 调用.delete()方法删除文章
    bbs.is_delete = 1
    # 完成删除后返回文章列表
    return redirect("bbs_list")

# 更新文章
"""
def bbs_update(request, id):
    # 获取需要修改的具体文章对象
    bbs = BBS.objects.get(id=id)
    # 判断用户是否为 POST 提交表单数据
    if request.method == "POST":
        # 将提交的数据赋值到表单实例中
        bbs_post_form = BBSForm(data=request.POST)
        # 判断提交的数据是否满足模型的要求
        if bbs_post_form.is_valid():
            # 保存新写入的 title、body 数据并保存
            bbs.title = request.POST['title']
            bbs.bbs_type = request.POST['bbs_type']
            bbs.content = request.POST['content']
            bbs.save()
            # 完成后返回到修改后的文章中。需传入文章的 id 值
            return redirect("bbs_detail", id=id)
        # 如果数据不合法，返回错误信息
        else:
            return HttpResponse("表单内容有误，请重新填写。")

    # 如果用户 GET 请求获取数据
    else:
        # 创建表单类实例
        bbs_post_form = BBSForm()
        # 赋值上下文，将 bbs 文章对象也传递进去，以便提取旧的内容
        context = { 'bbs': bbs, 'bbs_post_form': bbs_post_form }
        # 将响应返回到模板中
        return render(request, 'bbs/bbs_update.html', context)
"""
def bbs_update(request, id):
    bbs = BBS.objects.get(id = id)
    if request.method != 'POST':
        # 如果不是post,创建一个表单，并用instance=article当前数据填充表单
        form = BBSForm(instance=bbs) 
    else:
  # 如果是post,instance=article当前数据填充表单，并用data=request.POST获取到表单里的内容
        form = BBSForm(instance=bbs, data=request.POST)
        form.save() # 保存
        if form.is_valid(): # 验证
            return redirect('bbs_detail',bbs.pk) # 成功跳转
    return render(request, 'bbs/bbs_update.html', {'form':form,'bbs':bbs})