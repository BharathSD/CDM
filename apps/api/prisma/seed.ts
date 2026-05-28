import { PrismaClient, Role } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const adminPasswordHash = await bcrypt.hash("admin123", 10);

  const admin = await prisma.user.upsert({
    where: { username: "admin" },
    update: {},
    create: {
      username: "admin",
      passwordHash: adminPasswordHash,
      role: Role.ADMIN,
    },
  });

  await prisma.company.upsert({
    where: { cin: "U12345MH2020PTC000001" },
    update: {},
    create: {
      cin: "U12345MH2020PTC000001",
      name: "Acme Tax Services Pvt Ltd",
      type: "Private Limited",
      companyClass: "Company Limited by Shares",
      status: "active",
      city: "Mumbai",
      state: "Maharashtra",
      createdById: admin.id,
      updatedById: admin.id,
    },
  });

  console.log("Seed completed. Default admin username/password: admin/admin123");
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
