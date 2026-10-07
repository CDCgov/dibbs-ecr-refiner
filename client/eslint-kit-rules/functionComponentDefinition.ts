import type { RuleFunction } from '@eslint-react/kit';
import { merge } from '@eslint-react/kit';
import { AST_NODE_TYPES } from '@typescript-eslint/utils';

/** Enforce function-declarations for named components, and arrow-functions for unnamed components. */
export function functionComponentDefinition(): RuleFunction {
  return (context, { collect, hint }) => {
    const { query, visitor } = collect.components(context, {
      hint:
        hint.component.Default &
        ~hint.component.DoNotIncludeFunctionDefinedAsObjectMethod,
    });

    return merge(visitor, {
      'Program:exit'(program) {
        for (const { node } of query.all(program)) {
          const isNamed =
            (node.type === AST_NODE_TYPES.FunctionDeclaration &&
              node.id != null) ||
            node.parent.type === AST_NODE_TYPES.VariableDeclarator ||
            node.parent.type === AST_NODE_TYPES.Property;

          if (isNamed) {
            if (
              node.type === AST_NODE_TYPES.FunctionDeclaration ||
              node.parent.type === AST_NODE_TYPES.Property
            )
              continue;

            context.report({
              node,
              message:
                'Named function components must be defined with function declarations.',
              suggest: [
                {
                  desc: 'Convert to function declaration.',
                  fix(fixer) {
                    const src = context.sourceCode;
                    if (node.generator) return null;

                    if (
                      node.parent.type === AST_NODE_TYPES.VariableDeclarator
                    ) {
                      const varDecl = node.parent.parent;
                      if (
                        varDecl.type === AST_NODE_TYPES.VariableDeclaration &&
                        varDecl.declarations.length === 1
                      ) {
                        const name =
                          node.parent.id.type === AST_NODE_TYPES.Identifier
                            ? node.parent.id.name
                            : null;
                        if (!name) return null;

                        const prefix = node.async ? 'async ' : '';
                        const typeParams =
                          node.typeParameters != null
                            ? src.getText(node.typeParameters)
                            : '';
                        const params = `(${node.params.map((p) => src.getText(p)).join(', ')})`;
                        const returnType =
                          node.returnType != null
                            ? src.getText(node.returnType)
                            : '';

                        let bodyText = src.getText(node.body);
                        if (node.body.type !== AST_NODE_TYPES.BlockStatement) {
                          bodyText = `{ return ${bodyText}; }`;
                        }

                        return fixer.replaceText(
                          varDecl,
                          `${prefix}function ${name}${typeParams}${params}${returnType} ${bodyText}`
                        );
                      }
                    }
                    return null;
                  },
                },
              ],
            });
          } else {
            if (node.type === AST_NODE_TYPES.ArrowFunctionExpression) continue;

            context.report({
              node,
              message:
                'Unnamed function components must be defined with arrow functions.',
              suggest: [
                {
                  desc: 'Convert to arrow function.',
                  fix(fixer) {
                    const src = context.sourceCode;
                    if (node.generator) return null;

                    const prefix = node.async ? 'async ' : '';
                    const typeParams =
                      node.typeParameters != null
                        ? src.getText(node.typeParameters)
                        : '';
                    const params = `(${node.params.map((p) => src.getText(p)).join(', ')})`;
                    const returnType =
                      node.returnType != null
                        ? src.getText(node.returnType)
                        : '';
                    const body = src.getText(node.body);

                    if (
                      node.type === AST_NODE_TYPES.FunctionDeclaration &&
                      node.parent.type ===
                        AST_NODE_TYPES.ExportDefaultDeclaration
                    ) {
                      return fixer.replaceText(
                        node,
                        `${prefix}${typeParams}${params}${returnType} => ${body}`
                      );
                    }

                    if (node.type === AST_NODE_TYPES.FunctionExpression) {
                      return fixer.replaceText(
                        node,
                        `${prefix}${typeParams}${params}${returnType} => ${body}`
                      );
                    }

                    return null;
                  },
                },
              ],
            });
          }
        }
      },
    });
  };
}
