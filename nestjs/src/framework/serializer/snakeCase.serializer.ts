import { Expose } from "class-transformer";

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
