import requests
import json
import urllib.parse
import argparse

def get_introspection_query(url):
    query = '''
    query IntrospectionQuery {
        __schema {
            queryType {
                name
            }
            mutationType {
                name
            }
            types {
                ...FullType
            }
            directives {
                name
                description
                locations
                args {
                    ...InputValue
                }
            }
        }
    }

    fragment FullType on __Type {
        kind
        name
        description
        fields(includeDeprecated: true) {
            name
            description
            args {
                ...InputValue
            }
            type {
                ...TypeRef
            }
            isDeprecated
            deprecationReason
        }
        inputFields {
            ...InputValue
        }
        interfaces {
            ...TypeRef
        }
        enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
        }
        possibleTypes {
            ...TypeRef
        }
    }

    fragment InputValue on __InputValue {
        name
        description
        type {
            ...TypeRef
        }
        defaultValue
    }

    fragment TypeRef on __Type {
        kind
        name
        ofType {
            kind
            name
            ofType {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                kind
                                name
                            }
                        }
                    }
                }
            }
        }
    }
    '''
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json={'query': query}, headers=headers)
    try:
        response.raise_for_status()  # Check for HTTP errors
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {url}: {e}")
    except ValueError as e:
        print(f"Invalid JSON response received: {response.text}")

    return None

def construct_full_query(field_info):
    """Constructs a full query including all scalar fields."""
    field_name = field_info['name']
    args = ", ".join([f"{arg['name']}: <{arg['type']['name']}>" for arg in field_info.get('args', [])])
    sub_fields = ' '.join([sub_field['name'] for sub_field in field_info.get('type', {}).get('fields', []) if sub_field['type']['kind'] == 'SCALAR'])
    if not sub_fields:  # No subfields, just list the field
        return f"{field_name}({args})"
    return f"{field_name}({args}) {{ {sub_fields} }}"

def extract_queries_mutations(introspection_result, base_url):
    queries = []
    mutations = []

    for type_info in introspection_result['data']['__schema']['types']:
        if type_info['kind'] == 'OBJECT' and (type_info['name'] == 'Query' or type_info['name'] == 'Mutation'):
            for field in type_info.get('fields', []):
                complete_query = construct_full_query(field)
                query_type = 'mutation' if type_info['name'] == 'Mutation' else 'query'
                full_query_url = f"{base_url}?query={urllib.parse.quote(f'{query_type} {{{complete_query}}}')}"

                if query_type == 'query':
                    queries.append(full_query_url)
                else:
                    mutations.append(full_query_url)

    return queries, mutations

def main():
    parser = argparse.ArgumentParser(description='Extract and construct URLs for GraphQL queries and mutations.')
    parser.add_argument('-u', '--url', type=str, required=True, help='URL of the GraphQL API')

    args = parser.parse_args()
    base_url = args.url.rstrip('/')

    introspection_result = get_introspection_query(base_url)
    if introspection_result:
        queries, mutations = extract_queries_mutations(introspection_result, base_url)

        print("\nQuery URLs:")
        for query in queries:
            print(query)

        print("\nMutation URLs:")
        for mutation in mutations:
            print(mutation)

if __name__ == "__main__":
    main()
