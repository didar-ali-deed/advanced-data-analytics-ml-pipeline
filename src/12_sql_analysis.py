"""Stage 12: execute all documented business questions against SQLite."""

import pandas as pd

from utils.data_loader import save_frame, write_json, write_text
from utils.database import connect
from utils.questions import QUESTIONS, interpretation, load_queries
from utils.runner import stage_cli


def run(ctx):
    """Persist full query outputs and evidence-linked business interpretations."""
    queries = load_queries(ctx.root / "sql")
    outputs, answers = [], []
    with connect(ctx.path("data", "processed", "retail.sqlite")) as con:
        for name, sql in queries.items():
            frame = pd.read_sql_query(sql, con)
            output = save_frame(frame, ctx.path("reports", "exploratory", "sql", name + ".csv"))
            question, importance, action = QUESTIONS[name]
            answer = {
                "id": name,
                "question": question,
                "importance": importance,
                "query": sql,
                "output": output.relative_to(ctx.root).as_posix(),
                "interpretation": interpretation(name, frame),
                "potential_action": action,
                "preview": frame.head(5).to_dict("records"),
            }
            answers.append(answer)
            outputs.append(output)
    outputs.append(
        write_json(answers, ctx.path("reports", "business_insights", "sql_answers.json"))
    )
    markdown = "# Executed business questions\n\n"
    for answer in answers:
        markdown += (
            f"## {answer['question']}\n\n"
            f"**Importance:** {answer['importance']}\n\n"
            f"**Calculation:**\n\n```sql\n{answer['query']}\n```\n\n"
            + pd.DataFrame(answer["preview"]).to_markdown(index=False)
            + f"\n\n**Output:** [{answer['id']}](../../{answer['output']})\n\n"
            f"**Interpretation:** {answer['interpretation']}\n\n"
            f"**Potential action:** {answer['potential_action']}\n\n"
        )
    outputs.append(write_text(markdown, ctx.path("reports", "business_insights", "sql_answers.md")))
    return outputs


if __name__ == "__main__":
    stage_cli(12)
