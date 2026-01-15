require("dotenv").config();

const express = require("express");
const mysql = require("mysql2/promise");
const { Resend } = require("resend");
const fs = require("fs");

const app = express();
app.use(express.json());

const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
});

const resend = new Resend(process.env.RESEND_API_KEY);

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, service: "dnf-api-node" });
});

app.post("/api/lead", async (req, res) => {
  try {
    const { nome, email, empresa = "" } = req.body || {};

    if (!nome || !email) {
      return res.status(400).json({ error: "Nome e email são obrigatórios" });
    }

    // 1) Salvar no banco
    await pool.execute(
      "INSERT INTO leads (nome, email, empresa, recurso) VALUES (?, ?, ?, ?)",
      [nome, email, empresa, "Guia NR-1"]
    );

    // 2) Enviar email com PDF (Resend)
    const pdfPath = process.env.PDF_PATH;
    const pdfBase64 = fs.readFileSync(pdfPath).toString("base64");

    await resend.emails.send({
      from: process.env.EMAIL_FROM,
      to: email,
      subject: "📥 Seu Guia NR-1 - DNF Ocupacional",
      html: `
        <p>Olá, ${nome}!</p>
        <p>Segue em anexo o <strong>Guia NR-1</strong> que você solicitou.</p>
        <p>Se precisar de ajuda para adequação e implementação, é só responder este e-mail.</p>
        <br/>
        <p><strong>DNF Ocupacional</strong></p>
      `,
      attachments: [
        {
          filename: "Guia-NR1-DNF-Ocupacional.pdf",
          content: pdfBase64,
        },
      ],
    });

    return res.json({ success: true, saved: true, emailed: true });
  } catch (err) {
    return res.status(500).json({ error: String(err?.message || err) });
  }
});

const PORT = Number(process.env.PORT || 5001);
app.listen(PORT, "127.0.0.1", () => {
  console.log(`API Node rodando em http://127.0.0.1:${PORT}`);
});
