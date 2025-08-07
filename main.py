from ast import main
from multiprocessing.spawn import _main
import rich
import asyncio
from connection import config
from pydantic import BaseModel

from agents import (
    Agent,
    MessageOutputItem,
    OutputGuardrailTripwireTriggered,
    Runner,
    input_guardrail,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    output_guardrail,
)

class StudentsOutput(BaseModel):
    response: str
    isoutsidercome: bool

############################### Define Giaic_gatekeeper_guard as an Agent ###################################

Giaic_gatekeeper_guard = Agent(
    name="Giaic Security Guard",
    instructions=""" 
        Your task is to check every student's ID cards.
        If any outsider is detected, strictly stop them.
        """,
    output_type=StudentsOutput
)

###################################### Input guardrail function ############################################

@input_guardrail
async def security_guardrail(ctx, agent, input):
    result = await Runner.run(
        Giaic_gatekeeper_guard, 
        input, 
        run_config=config
    )
    rich.print(result.final_output)

    return GuardrailFunctionOutput(
        output_info=result.final_output.response,
        tripwire_triggered=result.final_output.isoutsidercome
    )

############################## Output guardrail function ############################################

@output_guardrail
async def security_guardrail_output(ctx, agent: Agent, output) -> GuardrailFunctionOutput:
    result = await Runner.run(
        Giaic_gatekeeper_guard, 
        output.response if isinstance(output, StudentsOutput) else output, 
        run_config=config
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output.response,
        tripwire_triggered=result.final_output.isoutsidercome
    )

######################################## Student agent ######################################################

student_agent = Agent(
    name="Student Agent",
    instructions="You are a student trying to enter GIAIC.",
    input_guardrails=[security_guardrail],  # Use function, not Agent
    output_guardrails=[security_guardrail_output]
)

################################# Main function ##################################################

async def main():
    try:
        result = await Runner.run(
            student_agent,
            "Hi! I am  student from GIAIC.",
            run_config=config
        )
        rich.print("Student entered GIAIC.")
        rich.print(result.final_output)

    except InputGuardrailTripwireTriggered:
        print("Gatekeeper blocked the student. Not from GIAIC!")
    except OutputGuardrailTripwireTriggered:
        print("Output guardrail blocked the response. Invalid output!")

if __name__ == "__main__":
    asyncio.run(main())