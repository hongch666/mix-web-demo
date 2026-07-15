import { Messages } from "src/common/constants";

/**
 * 构建验证码邮件 HTML 内容
 *
 * @param code 验证码
 * @param type 场景类型（register/login/reset）
 * @param expireMinutes 过期分钟数
 */
export function buildEmailContent(
  code: string,
  type: string,
  expireMinutes: number,
): string {
  const now = new Date();
  const formattedTime = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")} ${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;

  let title = Messages.EMAIL_VERIFICATION_CODE_SUBJECT;
  switch (type) {
    case "register":
      title = Messages.EMAIL_VERIFICATION_CODE_REGISTER_SUBJECT;
      break;
    case "login":
      title = Messages.EMAIL_VERIFICATION_CODE_LOGIN_SUBJECT;
      break;
    case "reset":
      title = Messages.EMAIL_VERIFICATION_CODE_RESET_SUBJECT;
      break;
  }

  return `<html><body style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); margin: 0; padding: 20px;'>
  <div style='max-width: 600px; margin: 0 auto; background: linear-gradient(145deg, #1e3a5f 0%, #2d4a6f 100%); border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0, 123, 255, 0.2); border: 1px solid rgba(64, 158, 255, 0.3);'>
    <!-- Header -->
    <div style='background: linear-gradient(135deg, #1e90ff 0%, #00bfff 100%); padding: 30px; text-align: center;'>
      <div style='font-size: 28px; margin-bottom: 10px;'>🧠</div>
      <h1 style='color: white; margin: 0; font-size: 22px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.2);'>IT智能文章推荐与知识问答系统</h1>
      <p style='color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 13px;'>基于 RAG 知识问答与权威文章 LLM 驱动推荐</p>
    </div>
    <!-- Content -->
    <div style='padding: 35px 40px; background-color: rgba(30, 42, 62, 0.95);'>
      <h2 style='color: #4db8ff; margin: 0 0 25px; font-size: 18px; text-align: center; font-weight: 500;'>${title}</h2>
      <p style='color: #b0c4de; font-size: 14px; line-height: 1.8; margin: 0 0 15px;'>尊敬的用户，您好！</p>
      <p style='color: #b0c4de; font-size: 14px; line-height: 1.8; margin: 0 0 25px;'>您正在使用 IT智能文章推荐与知识问答系统 的服务，本系统提供 IT 技术文章的智能推荐、RAG 大模型问答、用户互动交流等功能。</p>
      <p style='color: #b0c4de; font-size: 14px; line-height: 1.8; margin: 0 0 20px;'>您的邮箱验证码是：</p>
      <!-- Code Box -->
      <div style='background: linear-gradient(135deg, #1a5f7a 0%, #2e8baf 100%); padding: 25px; border-radius: 12px; margin: 25px 0; text-align: center; border: 1px solid rgba(77, 184, 255, 0.4); box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3), inset 0 1px 0 rgba(255,255,255,0.1);'>
        <strong style='font-size: 36px; color: #00ffff; letter-spacing: 8px; font-family: "Courier New", monospace; text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);'>${code}</strong>
      </div>
      <p style='color: #8899aa; font-size: 13px; line-height: 1.6; margin: 20px 0 10px; text-align: center;'>验证码有效期为 <strong style='color: #4db8ff;'>${expireMinutes} 分钟</strong>，请勿泄露给他人</p>
      <p style='color: #778899; font-size: 12px; line-height: 1.6; margin: 15px 0 0; text-align: center;'>如非本人操作，请忽略此邮件</p>
    </div>
    <!-- Features -->
    <div style='background-color: rgba(20, 30, 48, 0.9); padding: 25px 40px; border-top: 1px solid rgba(64, 158, 255, 0.2);'>
      <p style='color: #4db8ff; font-size: 13px; margin: 0 0 15px; text-align: center; font-weight: 500;'>系统功能</p>
      <div style='display: flex; justify-content: space-around; flex-wrap: wrap; text-align: center;'>
        <div style='margin: 8px;'><span style='color: #5ce1e6; font-size: 18px;'>📚</span><p style='color: #8899aa; font-size: 11px; margin: 5px 0 0;'>文章推荐</p></div>
        <div style='margin: 8px;'><span style='color: #5ce1e6; font-size: 18px;'>🤖</span><p style='color: #8899aa; font-size: 11px; margin: 5px 0 0;'>RAG问答</p></div>
        <div style='margin: 8px;'><span style='color: #5ce1e6; font-size: 18px;'>💬</span><p style='color: #8899aa; font-size: 11px; margin: 5px 0 0;'>用户互动</p></div>
        <div style='margin: 8px;'><span style='color: #5ce1e6; font-size: 18px;'>📊</span><p style='color: #8899aa; font-size: 11px; margin: 5px 0 0;'>统计分析</p></div>
      </div>
    </div>
    <!-- Footer -->
    <div style='background-color: rgba(15, 25, 40, 0.95); padding: 20px; text-align: center; border-top: 1px solid rgba(64, 158, 255, 0.15);'>
      <p style='color: #667788; font-size: 11px; line-height: 1.6; margin: 0 0 5px;'>此邮件由系统自动发送，请勿直接回复</p>
      <p style='color: #556677; font-size: 10px; line-height: 1.6; margin: 0;'>发送时间：${formattedTime} | MixWeb 多框架混合架构系统</p>
    </div>
  </div>
  </body></html>`;
}
