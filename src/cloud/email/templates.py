"""Templates de e-mail (v2.1)."""


def template_boas_vindas(tenant_nome: str, admin_email: str, trial_expira_em: str) -> str:
    """E-mail enviado no signup."""
    return f"""
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: white; padding: 32px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <h1 style="color: #1f6feb; margin-top: 0;">🌊 Bem-vindo ao FlowLog!</h1>
    <p>Olá, <strong>{tenant_nome}</strong>!</p>
    <p>Sua conta foi criada com sucesso. Você tem <strong>14 dias grátis</strong> (até <strong>{trial_expira_em}</strong>) pra testar todas as funcionalidades.</p>
    <h3>O que vem por aí:</h3>
    <ul>
      <li>📦 Cadastre seus produtos em segundos</li>
      <li>🔄 Registre entradas e saídas com histórico completo</li>
      <li>📊 Dashboard com KPIs em tempo real</li>
      <li>🔐 API REST pra integrações</li>
    </ul>
    <p style="margin: 32px 0;">
      <a href="https://app.flowlog.app/dashboard" style="background: #1f6feb; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; display: inline-block;">
        Acessar meu painel →
      </a>
    </p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 32px 0;" />
    <p style="font-size: 12px; color: #6b7280;">
      Dúvidas? Responda este e-mail.<br />
      FlowLog Cloud &middot; <a href="https://flowlog.app" style="color: #6b7280;">flowlog.app</a>
    </p>
  </div>
</body>
</html>
"""


def template_trial_expira(tenant_nome: str, dias_restantes: int) -> str:
    """E-mail de trial expirando (3 dias, 1 dia antes)."""
    urgencia = "URGENTE" if dias_restantes <= 1 else "Atenção"
    return f"""
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: white; padding: 32px; border-radius: 8px;">
    <h1 style="color: #cf222e; margin-top: 0;">⏰ {urgencia}: seu trial expira em {dias_restantes} dia(s)</h1>
    <p>Olá, <strong>{tenant_nome}</strong>!</p>
    <p>Seu trial gratuito do FlowLog está chegando ao fim. Pra continuar usando sem perder seus dados, escolha um plano:</p>
    <ul>
      <li><strong>Free</strong> — R$ 0/mês (1 usuário, 100 produtos)</li>
      <li><strong>Pro</strong> — R$ 99/mês (5 usuários, ilimitado)</li>
      <li><strong>Business</strong> — R$ 299/mês (50 usuários, API + white-label)</li>
    </ul>
    <p style="margin: 32px 0;">
      <a href="https://app.flowlog.app/billing" style="background: #1f6feb; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; display: inline-block;">
        Escolher plano →
      </a>
    </p>
  </div>
</body>
</html>
"""


def template_fatura_gerada(tenant_nome: str, numero: str, valor_reais: float, metodo: str, vencimento: str, pix_chave: str | None = None) -> str:
    """E-mail de fatura gerada (admin criou)."""
    pix_html = ""
    if pix_chave:
        pix_html = f"""
        <h3>Pagar via PIX</h3>
        <p style="background: #f3f4f6; padding: 12px; border-radius: 6px; font-family: monospace; word-break: break-all;">
          {pix_chave}
        </p>
        """
    return f"""
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: white; padding: 32px; border-radius: 8px;">
    <h1 style="color: #1f6feb; margin-top: 0;">💰 Nova fatura disponível</h1>
    <p>Olá, <strong>{tenant_nome}</strong>!</p>
    <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
      <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Número</strong></td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{numero}</td></tr>
      <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Valor</strong></td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">R$ {valor_reais:.2f}</td></tr>
      <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Método</strong></td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{metodo.upper()}</td></tr>
      <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Vencimento</strong></td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{vencimento}</td></tr>
    </table>
    {pix_html}
    <p style="font-size: 12px; color: #6b7280;">
      Após o pagamento, a confirmação leva até 1 dia útil (boleto) ou é instantânea (PIX).
    </p>
  </div>
</body>
</html>
"""


def template_fatura_paga(tenant_nome: str, numero: str, valor_reais: float) -> str:
    """E-mail de fatura paga (confirmação)."""
    return f"""
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: white; padding: 32px; border-radius: 8px;">
    <h1 style="color: #2da44e; margin-top: 0;">✅ Pagamento confirmado!</h1>
    <p>Olá, <strong>{tenant_nome}</strong>!</p>
    <p>Recebemos o pagamento da fatura <strong>{numero}</strong> no valor de <strong>R$ {valor_reais:.2f}</strong>.</p>
    <p>Obrigado por usar o FlowLog! 🌊</p>
  </div>
</body>
</html>
"""
