package routes

import (
	"gin_proj/controller"

	"github.com/gin-gonic/gin"
)

// SetupRouter 初始化路由
func SetupRouter() *gin.Engine {
	r := gin.Default()

	testGroup := r.Group("/api_gin")
	{
		//测试路由
		testGroup.GET("/gin", controller.TestController)
		//spring测试路由
		testGroup.GET("/spring", controller.JavaController)
		//nestjs测试路由
		testGroup.GET("/nestjs", controller.NestjsController)
		//测试ES同步MySQL
		testGroup.POST("/syncer", controller.SyncES)
	}
	userGroup := r.Group("/users")
	{
		//查询路由
		userGroup.GET("/", controller.GetUsersController)
		//新增路由
		userGroup.POST("/", controller.AddUserController)
		//删除路由
		userGroup.DELETE("/:id", controller.DeleteUserController)
		//根据id查询路由
		userGroup.GET("/:id", controller.GetUserByIdController)
		//修改路由
		userGroup.PUT("/", controller.UpdateUserController)
	}
	return r
}
