from crewai import Agent, Crew, Process, Task
import yaml
import os

class IdeaCrewService:
    def __init__(self):
        # Load agent and task configurations
        self.agents_config = self._load_config('config/agents.yaml')
        self.tasks_config = self._load_config('config/tasks.yaml')
        
    def _load_config(self, path):
        config_path = os.path.join(os.path.dirname(__file__), path)
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _get_llm_config(self, temperature=0.7):
        return {
            "model": "meta-70b",
            "provider": "groq",
            "temperature": temperature,
            "api_key": os.environ.get('GROQ_API_KEY')
        }

    def generate_story_concept(self, prompt, genre, mood, target_audience):
        try:
            # Create agents with proper LLM configuration
            concept_generator = Agent(
                role=self.agents_config['concept_generator']['role'].format(topic=genre),
                goal=self.agents_config['concept_generator']['goal'].format(topic=genre),
                backstory=self.agents_config['concept_generator']['backstory'].format(topic=genre),
                verbose=True,
                llm_config=self._get_llm_config(temperature=0.8)
            )
            
            world_builder = Agent(
                role=self.agents_config['world_builder']['role'].format(topic=genre),
                goal=self.agents_config['world_builder']['goal'].format(topic=genre),
                backstory=self.agents_config['world_builder']['backstory'].format(topic=genre),
                verbose=True,
                llm_config=self._get_llm_config(temperature=0.7)
            )
            
            plot_weaver = Agent(
                role=self.agents_config['plot_weaver']['role'].format(topic=genre),
                goal=self.agents_config['plot_weaver']['goal'].format(topic=genre),
                backstory=self.agents_config['plot_weaver']['backstory'].format(topic=genre),
                verbose=True,
                llm_config=self._get_llm_config(temperature=0.7)
            )

            # Create tasks with proper context lists
            generate_concepts_task = Task(
                description=self.tasks_config['generate_core_concepts']['description'],
                expected_output=self.tasks_config['generate_core_concepts']['expected_output'],
                agent=concept_generator,
                context=[
                    f"Generate a {genre} story concept with {mood} mood for {target_audience}.",
                    f"Story prompt: {prompt}",
                    "Provide a detailed response with clear sections for themes, narrative elements, and key story points."
                ]
            )

            develop_world_task = Task(
                description=self.tasks_config['develop_story_world']['description'],
                expected_output=self.tasks_config['develop_story_world']['expected_output'],
                agent=world_builder,
                context=[
                    "Based on the generated concept above, develop the story world.",
                    f"Consider the {genre} genre elements and {mood} atmosphere.",
                    "Detail the setting, environment, and world rules that support the story."
                ]
            )

            craft_plot_task = Task(
                description=self.tasks_config['craft_plot_possibilities']['description'],
                expected_output=self.tasks_config['craft_plot_possibilities']['expected_output'],
                agent=plot_weaver,
                context=[
                    "Using the established concept and world, outline the plot structure.",
                    f"Focus on creating a {mood} narrative that appeals to {target_audience}.",
                    "Include potential story arcs, conflicts, and character dynamics."
                ]
            )

            # Create and run the crew
            crew = Crew(
                agents=[concept_generator, world_builder, plot_weaver],
                tasks=[generate_concepts_task, develop_world_task, craft_plot_task],
                process=Process.sequential,
                verbose=True
            )

            # Execute crew and process results
            results = crew.kickoff()
            
            if not results:
                raise Exception("No results returned from crew execution")

            # Process results and ensure they are strings
            return {
                'core_concepts': str(results[0]) if results[0] else "",
                'story_world': str(results[1]) if len(results) > 1 and results[1] else "",
                'plot_possibilities': str(results[2]) if len(results) > 2 and results[2] else ""
            }

        except Exception as e:
            print(f"Error in story concept generation: {str(e)}")
            return None
