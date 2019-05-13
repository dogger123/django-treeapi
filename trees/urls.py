from django.urls import path,re_path
from . import views
# coding:utf-8
app_name = 'trees'
urlpatterns = [
	path('index/<int:tree_id>', views.index, name='index'),
    path('drawtree',views.drawTree,name='drawTree'),
    path('upload',views.upload),

    #path('dataset/<slug:dataset_id>', views.dataSet, name='dataset'),
    re_path(r'^dataset/(?P<dataset_id>[0-9a-z]*)', views.dataSet, name='dataset'),

    #path('tree/<int:tree_id>', views.tree, name='tree'),
    re_path(r'^tree/(?P<tree_id>[0-9a-z]*)', views.tree, name='tree'),

    #path('analysis/<int:analysis_id>', views.analysis, name='analysis'),
    re_path(r'^analysis/(?P<analysis_id>[0-9a-z]*)', views.analysis, name='analysis'),
	# path('api/import_trees', views.importTrees, name='importTrees'),
	# path('api/delete_trees', views.deleteTrees, name='deleteTrees'),
	# path('api/get_all_trees', views.getAllTrees, name='getAllTrees'),
	# path('api/get_tree_detail', views.getTreeDetail, name='getTreeDetail'),
	# path('api/show_ifelse', views.showIfElse, name='showIfElse'),
	# path('num_forecast', views.numForecast, name='getName'),
	path('condition_forecast', views.condForecast, name='condForecast'),
	path('advise', views.getAdvise, name='getAdvise'),
]