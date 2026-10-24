import { Expose } from "class-transformer";

/**
 * 将驼峰命名的键名转换为下划线命名
 */
export function toSnakeCase(key: string): string {
  return key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

/**
 * class-transformer 属性装饰器，将属性以驼峰转下划线后的名称对外暴露
 */
export function ExposeName(): PropertyDecorator {
  return (target: object, propertyKey: string | symbol) => {
    if (typeof propertyKey !== "string") {
      Expose()(target, propertyKey);
      return;
    }

    Expose({ name: toSnakeCase(propertyKey) })(target, propertyKey);
  };
}
