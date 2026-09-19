import asyncio

from backend.services.llm import LLMGateway


async def main():
    gateway = LLMGateway(
        provider="groq"
    )

    print("Provider info:")
    print(gateway.get_provider_info())

    if not gateway.is_configured():
        print(
            "ERROR: GROQ_API_KEY is not configured."
        )
        return

    print("\nTesting normal generation...")

    response = await gateway.generate(
        [
            {
                "role": "system",
                "content": (
                    "You are a concise technical "
                    "interview assistant."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Give me one short interview "
                    "question about Python."
                ),
            },
        ],
        temperature=0.3,
        max_tokens=200,
    )

    print("\nLLM response:")
    print(response)

    print("\nTesting structured JSON generation...")

    json_response = await gateway.generate_json(
        [
            {
                "role": "system",
                "content": (
                    "You generate structured "
                    "technical interview questions."
                ),
            },
            {
                "role": "user",
               "content": (
    "Return the answer as valid JSON. "
    "Generate one Python interview "
    "question with exactly these "
    "fields: question, category, "
    "difficulty."
),
            },
        ],
        temperature=0.2,
        max_tokens=300,
    )

    print("\nJSON response:")
    print(json_response)

    print("\nPHASE 4C TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())