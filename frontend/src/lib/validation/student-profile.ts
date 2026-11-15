import { z } from "zod";

const numberInput = z.union([z.string(), z.number()]);
const optionalInteger = (min: number, max?: number) => numberInput
  .optional()
  .transform(value => value === undefined || (typeof value === "string" && !value.trim()) ? null : Number(value))
  .pipe((max === undefined ? z.number().int().min(min) : z.number().int().min(min).max(max)).nullable());

export const profileSchema = z.object({
  branch: z.string().trim().min(1, "Branch is required").max(100),
  cgpa: numberInput.refine(value => typeof value === "number" || value.trim() !== "", "CGPA is required")
    .transform(Number).pipe(z.number().min(0, "Invalid CGPA").max(10, "Max 10")),
  phone: z.string().trim().min(1, "Phone number is required").max(20),
  graduation_year: optionalInteger(1900, 2100),
  active_backlogs: optionalInteger(0),
  linkedin_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  github_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  portfolio_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
});

export type ProfileFormInput = z.input<typeof profileSchema>;
export type ProfileFormData = z.output<typeof profileSchema>;
