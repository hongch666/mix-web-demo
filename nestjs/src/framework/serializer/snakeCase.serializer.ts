import { Expose } from "class-transformer";

/**
 * class-transformer 属性装饰器，将属性以驼峰转下划线后的名称对外暴露
 */
export function ExposeName(): PropertyDecorator {
  return (target: object, propertyKey: string | symbol) => {
    if (typeof propertyKey !== "string") {
      Expose()(target, propertyKey);
      return;
    }

    const name = propertyKey.replace(
      /[A-Z]/g,
      (letter) => `_${letter.toLowerCase()}`,
    );
    Expose({ name })(target, propertyKey);
  };
}
