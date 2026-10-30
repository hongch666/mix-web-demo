/**
 * OpenAPI 3.x → Markdown 导出器（浏览器端，无依赖）
 *
 * 输入是已经加载好的规范对象，输出一份可直接发给前端的 Markdown 文档；
 * 不读取任何预生成文件，内容完全来自当前 Swagger 页面加载的 /swagger/*.json
 *
 * 用法：
 *   var markdown = SwaggerMarkdownExport.build([
 *     { name: "Spring 服务", spec: specObject }
 *   ]);
 */
(function (root) {
  "use strict";

  var METHODS = ["get", "post", "put", "patch", "delete", "head", "options"];
  var MAX_DEPTH = 3;

  function isObject(value) {
    return value && typeof value === "object" && !Array.isArray(value);
  }

  function refName(schema) {
    if (
      isObject(schema) &&
      typeof schema.$ref === "string" &&
      schema.$ref.indexOf("#/components/schemas/") === 0
    ) {
      return schema.$ref.split("/").pop();
    }
    return null;
  }

  function mergeAllOf(schema, spec, seen) {
    if (!schema || !Array.isArray(schema.allOf)) {
      return schema || {};
    }
    var merged = { type: "object", properties: {}, required: [] };
    schema.allOf.forEach(function (item) {
      var part = resolveRef(item, spec, seen);
      if (isObject(part.properties)) {
        Object.keys(part.properties).forEach(function (key) {
          merged.properties[key] = part.properties[key];
        });
      }
      if (Array.isArray(part.required)) {
        merged.required = merged.required.concat(part.required);
      }
      if (part.description && !merged.description) {
        merged.description = part.description;
      }
    });
    if (schema.description) {
      merged.description = schema.description;
    }
    return merged;
  }

  function resolveRef(schema, spec, seen) {
    seen = seen || [];
    var name = refName(schema);
    if (!name) {
      return schema || {};
    }
    if (seen.indexOf(name) >= 0) {
      return { type: "object", description: "（递归引用）" };
    }
    var schemas = (spec.components || {}).schemas || {};
    var target = schemas[name];
    if (!isObject(target)) {
      return {};
    }
    return mergeAllOf(target, spec, seen.concat([name]));
  }

  function isNullable(schema) {
    if (!isObject(schema)) {
      return false;
    }
    if (schema.nullable === true) {
      return true;
    }
    if (schema.type === "null") {
      return true;
    }
    if (Array.isArray(schema.type) && schema.type.indexOf("null") >= 0) {
      return true;
    }
    var variants = schema.anyOf || schema.oneOf || [];
    for (var i = 0; i < variants.length; i += 1) {
      if (isObject(variants[i]) && variants[i].type === "null") {
        return true;
      }
    }
    return false;
  }

  function typeLabel(schema, spec, seen) {
    if (!isObject(schema)) {
      return "any";
    }
    seen = seen || [];

    var name = refName(schema);
    if (name) {
      var resolved = resolveRef(schema, spec, seen);
      if (resolved.type === "object" || resolved.properties) {
        return "`" + name + "`（对象）";
      }
      return "`" + name + "`";
    }

    if (Array.isArray(schema.anyOf) || Array.isArray(schema.oneOf)) {
      var labels = (schema.anyOf || schema.oneOf)
        .map(function (item) {
          return typeLabel(item, spec, seen);
        })
        .filter(function (label) {
          return label !== "null";
        });
      return unique(labels).join(" / ") || "any";
    }

    if (Array.isArray(schema.type)) {
      var filtered = schema.type.filter(function (item) {
        return item !== "null";
      });
      return unique(filtered).join(" / ") || "any";
    }

    if (schema.type === "array") {
      return "array<" + typeLabel(schema.items || {}, spec, seen) + ">";
    }
    if (isObject(schema.additionalProperties)) {
      return "object<string, " + typeLabel(schema.additionalProperties, spec, seen) + ">";
    }
    if (schema.type === "object" || schema.properties) {
      return "object";
    }
    var base = schema.type || "any";
    return schema.format ? base + "(" + schema.format + ")" : base;
  }

  function unique(list) {
    return list.filter(function (item, index) {
      return list.indexOf(item) === index;
    });
  }

  function escapeCell(text) {
    return String(text == null ? "" : text)
      .replace(/\r?\n/g, " ")
      .replace(/\|/g, "\\|")
      .trim();
  }

  function describeField(schema, resolved, spec, seen) {
    var parts = [];
    var description = (resolved && resolved.description) || (schema && schema.description) || "";
    description = escapeCell(description);
    if (description) {
      parts.push(description);
    }
    var enums = (resolved && resolved.enum) || (schema && schema.enum);
    if (Array.isArray(enums) && enums.length) {
      parts.push(
        "可选值：" +
          enums
            .slice(0, 10)
            .map(function (item) {
              return "`" + item + "`";
            })
            .join("、"),
      );
    }
    if (resolved && resolved.default !== undefined) {
      parts.push("默认 `" + resolved.default + "`");
    }
    if (isNullable(schema) || isNullable(resolved)) {
      parts.push("可为空");
    }
    return parts.join("；");
  }

  function flattenFields(schema, spec, prefix, depth, seen) {
    if (depth > MAX_DEPTH) {
      return [];
    }
    prefix = prefix || "";
    depth = depth || 0;
    seen = seen || [];

    var name = refName(schema);
    if (name) {
      if (seen.indexOf(name) >= 0) {
        return [];
      }
      schema = resolveRef(schema, spec, seen);
      seen = seen.concat([name]);
    }
    if (!isObject(schema)) {
      return [];
    }
    schema = mergeAllOf(schema, spec, seen);
    var properties = schema.properties || {};
    var required = schema.required || [];
    var rows = [];

    Object.keys(properties).forEach(function (fieldName) {
      var fieldSchema = isObject(properties[fieldName]) ? properties[fieldName] : {};
      var resolved = resolveRef(fieldSchema, spec, seen);
      rows.push([
        "`" + prefix + fieldName + "`",
        typeLabel(fieldSchema, spec, seen),
        required.indexOf(fieldName) >= 0 ? "是" : "否",
        describeField(fieldSchema, resolved, spec, seen),
      ]);

      var nested = resolved;
      var nestedPrefix = prefix + fieldName + ".";
      if (resolved.type === "array") {
        var itemsName = refName(resolved.items);
        if (itemsName && seen.indexOf(itemsName) >= 0) {
          return;
        }
        nested = resolveRef(resolved.items || {}, spec, seen);
        nestedPrefix = prefix + fieldName + "[].";
      }
      if (isObject(nested.properties) && Object.keys(nested.properties).length) {
        rows = rows.concat(flattenFields(nested, spec, nestedPrefix, depth + 1, seen));
      }
    });
    return rows;
  }

  function exampleValue(schema, spec, depth, seen) {
    depth = depth || 0;
    seen = seen || [];
    if (depth > 4 || !isObject(schema)) {
      return null;
    }
    if (schema.example !== undefined) {
      return schema.example;
    }
    if (Array.isArray(schema.examples) && schema.examples.length) {
      return schema.examples[0];
    }

    var name = refName(schema);
    if (name) {
      if (seen.indexOf(name) >= 0) {
        return {};
      }
      return exampleValue(resolveRef(schema, spec, seen), spec, depth, seen.concat([name]));
    }
    if (Array.isArray(schema.allOf)) {
      return exampleValue(mergeAllOf(schema, spec, seen), spec, depth, seen);
    }
    if (Array.isArray(schema.anyOf) || Array.isArray(schema.oneOf)) {
      var variants = (schema.anyOf || schema.oneOf).filter(function (item) {
        return typeLabel(item, spec) !== "null";
      });
      return variants.length ? exampleValue(variants[0], spec, depth, seen) : null;
    }
    if (Array.isArray(schema.enum) && schema.enum.length) {
      return schema.enum[0];
    }

    var rawType = schema.type;
    if (Array.isArray(rawType)) {
      rawType = rawType.filter(function (item) {
        return item !== "null";
      })[0] || "null";
    }
    if (rawType === "object" || schema.properties) {
      var result = {};
      Object.keys(schema.properties || {})
        .slice(0, 12)
        .forEach(function (key) {
          result[key] = exampleValue(schema.properties[key], spec, depth + 1, seen);
        });
      return result;
    }
    if (rawType === "array") {
      return [exampleValue(schema.items || {}, spec, depth + 1, seen)];
    }
    if (rawType === "integer") {
      return 0;
    }
    if (rawType === "number") {
      return 0.0;
    }
    if (rawType === "boolean") {
      return true;
    }
    if (rawType === "null") {
      return null;
    }
    if (schema.format === "date-time") {
      return "2026-01-01T00:00:00Z";
    }
    if (schema.format === "date") {
      return "2026-01-01";
    }
    return "string";
  }

  function table(headers, rows) {
    var lines = [
      "| " + headers.join(" | ") + " |",
      "| " + headers.map(function () { return "---"; }).join(" | ") + " |",
    ];
    rows.forEach(function (row) {
      lines.push(
        "| " +
          row
            .map(function (cell) {
              var text = escapeCell(cell);
              return text || "-";
            })
            .join(" | ") +
          " |",
      );
    });
    return lines;
  }

  function pushTable(lines, headers, rows) {
    table(headers, rows).forEach(function (line) {
      lines.push(line);
    });
    lines.push("");
  }

  function renderOperation(serviceName, path, method, operation, spec) {
    var lines = ["### `" + method.toUpperCase() + " " + path + "`", ""];
    var summary = (operation.summary || "").trim();
    var description = (operation.description || "").trim();

    if (summary) {
      lines.push("**" + escapeCell(summary) + "**", "");
    }
    if (description) {
      description.split(/\n{2,}/).forEach(function (paragraph) {
        var text = paragraph.trim();
        if (text) {
          lines.push(text, "");
        }
      });
    }

    pushTable(lines, ["项目", "值"], [
      ["方法与路径", "`" + method.toUpperCase() + "` `" + path + "`"],
      ["接口分组", (operation.tags || []).join("、") || "-"],
      ["所属服务", serviceName],
    ]);

    var parameters = (operation.parameters || []).filter(isObject);
    [
      ["路径参数", parameters.filter(function (item) { return item.in === "path"; })],
      ["查询参数", parameters.filter(function (item) { return item.in === "query"; })],
      ["请求头参数", parameters.filter(function (item) { return item.in === "header"; })],
    ].forEach(function (group) {
      if (!group[1].length) {
        return;
      }
      var rows = group[1].map(function (item) {
        var schema = item.schema || {};
        return [
          "`" + item.name + "`",
          typeLabel(schema, spec),
          item.required ? "是" : "否",
          escapeCell(item.description || schema.description || ""),
        ];
      });
      lines.push("**" + group[0] + "**", "");
      pushTable(lines, ["参数", "类型", "必填", "说明"], rows);
    });

    var content = (operation.requestBody || {}).content || {};
    Object.keys(content).forEach(function (mediaType) {
      var schema = (content[mediaType] || {}).schema || {};
      lines.push("**请求体**（`" + mediaType + "`）", "");
      var fields = flattenFields(schema, spec);
      if (fields.length) {
        pushTable(lines, ["字段", "类型", "必填", "说明"], fields);
      } else {
        lines.push("类型：" + typeLabel(schema, spec), "");
      }
      if (mediaType === "multipart/form-data") {
        lines.push("表单上传，类型为 `file` 的字段需要以文件字段提交。", "");
      } else {
        var sample = exampleValue(schema, spec);
        if (sample !== null) {
          lines.push("```json", JSON.stringify(sample, null, 2), "```", "");
        }
      }
    });

    var responses = operation.responses || {};
    lines.push("**响应**", "");
    Object.keys(responses)
      .sort(function (a, b) {
        var aNum = /^\d+$/.test(a);
        var bNum = /^\d+$/.test(b);
        if (aNum !== bNum) {
          return aNum ? -1 : 1;
        }
        return a < b ? -1 : a > b ? 1 : 0;
      })
      .forEach(function (statusCode) {
        var response = responses[statusCode] || {};
        var desc = escapeCell(response.description || "");
        lines.push(("`" + statusCode + "` " + desc).trim(), "");

        var responseContent = response.content || {};
        if (responseContent["text/event-stream"]) {
          responseContent = { "text/event-stream": responseContent["text/event-stream"] };
        }
        Object.keys(responseContent).forEach(function (mediaType) {
          var schema = (responseContent[mediaType] || {}).schema || {};
          if (!isObject(schema) || !Object.keys(schema).length) {
            return;
          }
          var isStream = mediaType === "text/event-stream";
          if (isStream) {
            lines.push("SSE 流式响应（`" + mediaType + "`），逐帧返回，单帧结构如下：", "");
          }
          var fields = flattenFields(schema, spec);
          if (fields.length) {
            pushTable(lines, ["字段", "类型", "必填", "说明"], fields);
          }
          if (
            isStream ||
            mediaType === "*/*" ||
            mediaType === "application/json" ||
            mediaType === "application/*"
          ) {
            var sample = exampleValue(schema, spec);
            if (sample !== null) {
              lines.push("```json", JSON.stringify(sample, null, 2), "```", "");
            }
          }
        });
      });
    lines.push("");
    return lines;
  }

  function renderService(service, spec) {
    var info = spec.info || {};
    var paths = spec.paths || {};
    var operations = [];
    Object.keys(paths).forEach(function (path) {
      METHODS.forEach(function (method) {
        if (isObject(paths[path]) && isObject(paths[path][method])) {
          operations.push({ path: path, method: method, operation: paths[path][method] });
        }
      });
    });

    var lines = ["## " + service.name, ""];
    if (info.description || info.title) {
      lines.push("> " + escapeCell(info.description || info.title), "");
    }
    pushTable(lines, ["项目", "值"], [
      ["服务标识", "`" + (info.title || service.name) + "`"],
      ["OpenAPI 版本", spec.openapi || "-"],
      ["接口数量", operations.length + " 个（" + Object.keys(paths).length + " 条路径）"],
    ]);

    operations.forEach(function (item) {
      lines = lines.concat(renderOperation(service.name, item.path, item.method, item.operation, spec));
    });
    return lines;
  }

  function build(services, options) {
    options = options || {};
    var now = new Date();
    var timestamp =
      now.getFullYear() +
      "-" +
      pad(now.getMonth() + 1) +
      "-" +
      pad(now.getDate()) +
      " " +
      pad(now.getHours()) +
      ":" +
      pad(now.getMinutes());

    var total = 0;
    var overview = [];
    var body = [];

    services.forEach(function (service) {
      var spec = service.spec || {};
      var count = 0;
      Object.keys(spec.paths || {}).forEach(function (path) {
        METHODS.forEach(function (method) {
          if (isObject(spec.paths[path]) && isObject(spec.paths[path][method])) {
            count += 1;
          }
        });
      });
      total += count;
      var specTitle = (spec.info || {}).title || "-";
      overview.push([service.name, "`" + specTitle + "`", String(count)]);
      body = body.concat(renderService(service, spec));
    });

    var header = [
      "# 项目接口文档",
      "",
      "> 由网关 Swagger 页面导出（" + timestamp + "），数据来源为各服务实时 OpenAPI 规范",
      ">",
      "> 统一入口：网关地址，除公开接口外请求头需要 `Authorization: Bearer <token>`",
      "",
      "## 使用说明",
      "",
      "1. 所有请求走网关统一入口，按各接口路径直接拼接网关地址。",
      "2. 除登录、注册、验证码等公开接口外，请求头需携带 `Authorization: Bearer <token>`；网关校验通过后向下游透传 `X-User-Id`、`X-Username`、`X-Session-Id`。",
      "3. 响应统一为 `{\"code\": 200, \"msg\": \"success\", \"data\": ...}`，`code` 为 3 位 HTTP 状态码。",
      "4. 字段类型若显示为 `` `XxxVO`（对象） ``，表示引用规范 `components/schemas` 中的结构，字段表已展开常用层级。",
      "",
      "## 服务概览",
      "",
    ];
    header = header.concat(table(["服务", "标识", "接口数"], overview));
    header.push("", "合计 " + total + " 个接口。", "", "---", "");
    return header.concat(body).join("\n") + "\n";
  }

  function pad(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function fileName() {
    var now = new Date();
    return (
      "mix-web-demo-api-" +
      now.getFullYear() +
      pad(now.getMonth() + 1) +
      pad(now.getDate()) +
      ".md"
    );
  }

  root.SwaggerMarkdownExport = { build: build, fileName: fileName };
})(typeof window !== "undefined" ? window : globalThis);
