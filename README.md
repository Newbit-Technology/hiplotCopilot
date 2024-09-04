# hiplotCopilot

基于 https://github.com/hiplot/hiplotCopilot 完善了绘图功能。

绘制功能依赖于milvus向量数据库进行多模态检索，可通过`docker-compose up -d`一键部署，部署完成后执行`make init_plugin`将文档数据写入milvus
