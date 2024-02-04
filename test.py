#%%
from pipeline.qa import hiplot_doc_qa_pipeline
#%%
print(hiplot_doc_qa_pipeline("Hiplot是什么？").get()[0])
#%%
print(hiplot_doc_qa_pipeline("Hiplot目前支持哪些绘图工具").get()[0])
#%%
