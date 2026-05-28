import express from "express";
import cors from "cors";
import bcrypt from "bcryptjs";
import { Role } from "@prisma/client";
import { z } from "zod";
import { config } from "./config.js";
import { prisma } from "./prisma.js";
import { authenticate, authorize, signToken } from "./auth.js";

const app = express();

app.use(cors());
app.use(express.json());

const companySchema = z.object({
  cin: z.string().min(5).max(32),
  name: z.string().min(2).max(120),
  type: z.string().min(2).max(80),
  companyClass: z.string().min(2).max(120),
  status: z.string().min(2).max(50).default("active"),
  registrationDate: z.string().datetime().optional().nullable(),
  contactEmail: z.string().email().optional().nullable(),
  contactPhone: z.string().max(20).optional().nullable(),
  registeredAddress: z.string().max(400).optional().nullable(),
  city: z.string().max(100).optional().nullable(),
  state: z.string().max(100).optional().nullable(),
  pincode: z.string().max(20).optional().nullable(),
  panNumber: z.string().max(20).optional().nullable(),
  gstNumber: z.string().max(30).optional().nullable(),
  notes: z.string().max(2000).optional().nullable(),
});

const companyUpdateSchema = companySchema.partial().extend({
  cin: z.string().min(5).max(32).optional(),
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.post("/auth/login", async (req, res) => {
  const parsed = z
    .object({ username: z.string().min(3), password: z.string().min(6) })
    .safeParse(req.body);

  if (!parsed.success) {
    res.status(400).json({ message: "Invalid login request", errors: parsed.error.flatten() });
    return;
  }

  const user = await prisma.user.findUnique({ where: { username: parsed.data.username } });
  if (!user) {
    res.status(401).json({ message: "Invalid username or password" });
    return;
  }

  const isValid = await bcrypt.compare(parsed.data.password, user.passwordHash);
  if (!isValid) {
    res.status(401).json({ message: "Invalid username or password" });
    return;
  }

  const token = signToken({ id: user.id, username: user.username, role: user.role });
  res.json({
    token,
    user: { id: user.id, username: user.username, role: user.role },
  });
});

app.get("/auth/me", authenticate, async (req, res) => {
  const user = await prisma.user.findUnique({ where: { id: req.user!.id } });
  if (!user) {
    res.status(404).json({ message: "User not found" });
    return;
  }

  res.json({ id: user.id, username: user.username, role: user.role });
});

app.get("/companies", authenticate, authorize([Role.ADMIN, Role.EDITOR, Role.VIEWER]), async (req, res) => {
  const query = typeof req.query.query === "string" ? req.query.query.trim() : "";
  const page = Math.max(Number(req.query.page ?? 1) || 1, 1);
  const pageSize = Math.min(Math.max(Number(req.query.pageSize ?? 10) || 10, 1), 100);

  const where = query
    ? {
        OR: [
          { cin: { contains: query } },
          { name: { contains: query } },
        ],
      }
    : undefined;

  const [items, total] = await Promise.all([
    prisma.company.findMany({
      where,
      orderBy: { updatedAt: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
    }),
    prisma.company.count({ where }),
  ]);

  res.json({ items, total, page, pageSize });
});

app.post("/companies", authenticate, authorize([Role.ADMIN, Role.EDITOR]), async (req, res) => {
  const parsed = companySchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ message: "Invalid company data", errors: parsed.error.flatten() });
    return;
  }

  const payload = parsed.data;

  const existingCin = await prisma.company.findUnique({ where: { cin: payload.cin } });
  if (existingCin) {
    res.status(409).json({ message: "Company with this CIN already exists" });
    return;
  }

  const company = await prisma.company.create({
    data: {
      ...payload,
      registrationDate: payload.registrationDate ? new Date(payload.registrationDate) : null,
      createdById: req.user!.id,
      updatedById: req.user!.id,
    },
  });

  res.status(201).json(company);
});

app.put("/companies/:id", authenticate, authorize([Role.ADMIN, Role.EDITOR]), async (req, res) => {
  const parsed = companyUpdateSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ message: "Invalid company data", errors: parsed.error.flatten() });
    return;
  }

  const id = req.params.id;
  const existing = await prisma.company.findUnique({ where: { id } });
  if (!existing) {
    res.status(404).json({ message: "Company not found" });
    return;
  }

  if (parsed.data.cin && parsed.data.cin !== existing.cin) {
    const duplicate = await prisma.company.findUnique({ where: { cin: parsed.data.cin } });
    if (duplicate) {
      res.status(409).json({ message: "Another company already uses this CIN" });
      return;
    }
  }

  const company = await prisma.company.update({
    where: { id },
    data: {
      ...parsed.data,
      registrationDate:
        parsed.data.registrationDate === undefined
          ? undefined
          : parsed.data.registrationDate
            ? new Date(parsed.data.registrationDate)
            : null,
      updatedById: req.user!.id,
    },
  });

  res.json(company);
});

app.listen(config.port, () => {
  console.log(`API listening on http://localhost:${config.port}`);
});
