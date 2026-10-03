{{/*
本文件是 model-gen.tpl 中 {{.customized}} 的注入点，用于往自动生成的 <table>_gen.go 末尾追加方法
保持空文件：业务方法一律写在 <table>.go 的 custom<Table>Model 中，不要写到这里
原因：_gen.go 带 DO NOT EDIT 标记，任何手写内容都会在下次 goctl model ddl 时丢失
*/}}
