def get_breadcrumb(category):
    """
    面包屑导航
    :param category: 当前选择的三级分类
    :return:
    """
    # 获取一级类别
    cat1 = category.parent.parent
    # 给一级类别指定一个url
    cat1.url = cat1.goodschannel_set.all()[0].url
    breadcrumb = {
        'cat1': cat1,
        'cat2': category.parent,
        'cat3': category
    }

    return breadcrumb
