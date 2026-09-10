from neomodel import AsyncStructuredRel


class PublishedByRel(AsyncStructuredRel):
    """Article -[:PUBLISHED_BY]-> User 关系（无属性）

    neomodel 的 traverse()/resolve_subgraph() 预加载要求关系必须有关系模型类，即使没有属性也要显式定义，否则无法解析关系对象
    """
