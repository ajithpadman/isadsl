import { describe, test, expect } from "vitest";

/*
let services: ReturnType<typeof createIsaServices>;
let parse:    ReturnType<typeof parseHelper<ISASpec>>;
let document: LangiumDocument<ISASpec> | undefined;

beforeAll(async () => {
    services = createIsaServices(EmptyFileSystem);
    const doParse = parseHelper<ISASpec>(services.Isa);
    parse = (input: string) => doParse(input, { validation: true });

    // activate the following if your linking test requires elements from a built-in library, for example
    // await services.shared.workspace.WorkspaceManager.initializeWorkspace([]);
});
*/

describe('Validating', () => {

    test('Placeholder - TODO: Add validation tests', () => {
        // TODO: Add validation tests
        expect(true).toBe(true);
    });
});
