import {z} from "zod";

export const lessonSchema = z.object({
  title: z.string(), duration_seconds: z.number().positive(),
  scenes: z.array(z.object({start: z.number(), end: z.number(), title: z.string(), body: z.string()})).min(1),
});
export const recapPropsSchema = z.object({lesson: lessonSchema, narrationPath: z.string().nullable()});
export type RecapProps = z.infer<typeof recapPropsSchema>;
