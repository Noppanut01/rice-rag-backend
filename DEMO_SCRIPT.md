# Rice Expert Demo Script

## Manual Demo Flow

1. Guest opens landing page.
   Expected: Shows system intro, supported rice varieties, AI chat, and public knowledge documents.

2. Guest asks AI a basic rice question.
   Expected: AI answers in Thai. Explain that login is needed to save chat history and create plans.

3. User registers or logs in.
   Expected: Redirects to `/app/plots`.

4. User creates a plan.
   Use: select rice variety, choose valid start date, fill plot name, area, soil type, and planting method.
   Expected: Plan is created and appears in the plots list.

5. User opens plot dashboard.
   Expected: Shows current crop stage, time-based progress, resources, fertilizer formulas, and task checklist.

6. User ticks a task.
   Expected: Task changes to completed and remains completed after page refresh because it is saved in `plan_tasks.is_completed`.

7. User edits plot area or soil type.
   Expected: Seed/fertilizer resources recalculate, while task list and completed status remain unchanged.

8. User opens calendar.
   Expected: Calendar marks dates that have tasks and shows task details for the selected date.

9. User asks floating AI chat about the current plot.
   Expected: AI receives plan context such as variety, soil, stage, today tasks, and upcoming tasks.

10. User clones the plan.
    Expected: New plan is generated from a new start date using the same variety, method, area, and soil.

11. Admin logs in.
    Expected: Admin sees the system management menu. Normal users cannot open `/app/admin` directly.

12. Admin manages rice varieties.
    Expected: Required fields validate before saving. Fertilizer during tillering uses soil automatically; fertilizer during panicle initiation uses the variety formula.

13. Admin uploads knowledge documents.
    Expected: Documents are grouped by collection and used by RAG after ingestion.

14. Admin manages prompt templates and knowledge gaps.
    Expected: Templates appear as suggested questions; gaps show questions with weak/no document support.

## Explanation For Committee

The generated plan is a baseline schedule, not a rigid real-world command. Rice farming can be delayed by rain, water availability, labor, pests, or field conditions.

The system separates two kinds of tracking:

- Time progress: the circular percentage shows where the plan should be in the crop cycle based on dates.
- Work completion: the checklist records whether each task was actually done and persists it in the database.

If real work is delayed, unfinished past tasks appear as overdue. The user can tick them when completed. If the whole production cycle needs to move, the user can clone or create a new plan from a new start date.
