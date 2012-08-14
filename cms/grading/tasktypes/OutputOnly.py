#!/usr/bin/python
# -*- coding: utf-8 -*-

# Programming contest management system
# Copyright © 2010-2012 Giovanni Mascellani <mascellani@poisson.phc.unipi.it>
# Copyright © 2010-2012 Stefano Maggiolo <s.maggiolo@gmail.com>
# Copyright © 2010-2012 Matteo Boscariol <boscarim@hotmail.com>
# Copyright © 2012 Luca Wehrstedt <luca.wehrstedt@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Task type for output only tasks.

"""

from cms.grading.TaskType import TaskType, \
     create_sandbox, delete_sandbox
from cms.grading.ParameterTypes import ParameterTypeChoice
from cms.grading import white_diff_step, evaluation_step, \
    extract_outcome_and_text


class OutputOnly(TaskType):
    """Task type class for output only tasks, with submission composed
    of testcase_number text files, to be evaluated diffing or using a
    comparator.

    Parameters are a list of string with one element (for future
    possible expansions), which maybe 'diff' or 'comparator', meaning that
    the evaluation is done via white diff or via a comparator.

    """
    ALLOW_PARTIAL_SUBMISSION = True

    _EVALUATION = ParameterTypeChoice(
        "Output evaluation",
        "output_eval",
        "",
        {"diff": "Outputs compared with white diff",
         "comparator": "Outputs are compared by a comparator"})

    ACCEPTED_PARAMETERS = [_EVALUATION]

    @property
    def name(self):
        """See TaskType.name."""
        # TODO add some details if a comparator is used, etc...
        return "Output only"

    def get_compilation_commands(self, submission_format):
        """See TaskType.get_compilation_commands."""
        return None

    def compile(self):
        """See TaskType.compile."""
        # No compilation needed.
        self.job.success = True
        self.job.compilation_success = True
        self.job.text = "No compilation needed."

    def evaluate_testcase(self, test_number):
        """See TaskType.evaluate_testcase."""
        sandbox = create_sandbox(self)
        self.job.sandboxes.append(sandbox.path)

        # Immediately prepare the skeleton to return
        self.job.evaluations[test_number] = {'sandboxes': [sandbox.path],
                                             'plus': {}}
        evaluation = self.job.evaluations[test_number]
        outcome = None
        text = None

        # Since we allow partial submission, if the file is not
        # present we report that the outcome is 0.
        if "output_%03d.txt" % test_number not in self.job.files:
            evaluation['success'] = True
            evaluation['outcome'] = 0.0
            evaluation['text'] = "File not submitted."
            return True

        # First and only one step: diffing (manual or with manager).
        output_digest = self.job.files["output_%03d.txt" %
                                       test_number].digest

        # Put the files into the sandbox
        sandbox.create_file_from_storage(
            "res.txt",
            self.job.testcases[test_number].output)
        sandbox.create_file_from_storage(
            "output.txt",
            output_digest)

        # TODO: this should check self.parameters, not managers.
        if len(self.job.managers) == 0:
            # No manager: I'll do a white_diff between the submission
            # file and the correct output res.txt.
            success = True
            outcome, text = white_diff_step(
                sandbox, "output.txt", "res.txt")

        else:
            # Manager present: wonderful, he'll do all the job.
            manager_filename = self.job.managers.keys()[0]
            sandbox.create_file_from_storage(
                manager_filename,
                self.job.managers[manager_filename].digest,
                executable=True)
            success, _ = evaluation_step(
                sandbox,
                ["./%s" % manager_filename,
                 "input.txt", "res.txt", "output.txt"],
                allow_path=["input.txt", "output.txt", "res.txt"])
            if success:
                outcome, text = extract_outcome_and_text(sandbox)

        # Whatever happened, we conclude.
        evaluation['success'] = success
        evaluation['outcome'] = outcome
        evaluation['text'] = text
        delete_sandbox(sandbox)
        return success
